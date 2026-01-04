"""
Bot event handlers.
Handles chat member updates (bot added/removed), chat migration.
"""
from aiogram import Router, types, Bot, F
from aiogram.enums import ChatMemberStatus

from database import (
    get_chat_language, delete_schedule, register_group, count_groups
)
from constants.messages import Messages
from handlers.common import escape_html
import os
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.my_chat_member()
async def on_my_chat_member_update(update: types.ChatMemberUpdated, bot: Bot):
    """Handle bot being added/removed from groups."""
    
    # Detect if bot was removed/kicked
    if update.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
        chat_id = update.chat.id
        title = update.chat.title or "Unknown"
        
        # Clean database
        delete_schedule(chat_id)
        
        # Notify bot owner
        admin_id = os.getenv("ADMIN_ID")
        if admin_id:
            try:
                lang = get_chat_language(chat_id) or "UZ"
                username = update.chat.username
                
                # Determine Public/Private
                vis_type = "public" if username else "private"
                type_icon = "🌐" if vis_type == "public" else "🔒"
                username_link = f"<a href='https://t.me/{username}'>@{username}</a>" if username else ""
                
                total_groups = count_groups()
                await bot.send_message(
                    chat_id=admin_id,
                    text=Messages.get("BOT_KICKED", lang).format(
                        title=escape_html(title), 
                        chat_id=chat_id, 
                        total_groups=total_groups,
                        type_icon=type_icon,
                        username_link=username_link
                    )
                )
                logger.info(f"Bot removed from group {chat_id} ({title})")
            except Exception as e:
                logger.error(f"Failed to notify admin about removal from {chat_id}: {e}")

    # Detect if bot joined a new group
    elif update.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        # Only notify if it wasn't already a member
        if update.old_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.RESTRICTED]:
            chat_id = update.chat.id
            title = update.chat.title or "Unknown"
            username = update.chat.username
            
            # Determine Public/Private
            vis_type = "public" if username else "private"
            
            # Register group in DB
            register_group(chat_id, title, vis_type, username)
            
            # Notify bot owner
            admin_id = os.getenv("ADMIN_ID")
            if admin_id:
                try:
                    count = await bot.get_chat_member_count(chat_id)
                    total_groups = count_groups()
                    
                    type_icon = "🌐" if vis_type == "public" else "🔒"
                    username_link = f"<a href='https://t.me/{username}'>@{username}</a>" if username else ""

                    await bot.send_message(
                        chat_id=admin_id,
                        text=Messages.get("BOT_ADDED", "UZ").format(
                            title=escape_html(title), 
                            chat_id=chat_id, 
                            count=count, 
                            total_groups=total_groups,
                            type_icon=type_icon,
                            username_link=username_link
                        )
                    )
                    logger.info(f"Bot added to group {chat_id} ({title})")
                except Exception as e:
                    logger.error(f"Failed to notify admin about new group {chat_id}: {e}")


@router.message(F.migrate_to_chat_id)
async def on_chat_migrate(message: types.Message):
    """
    Handle chat migration (group → supergroup).
    Telegram changes chat_id when a group is upgraded to supergroup.
    """
    old_chat_id = message.chat.id
    new_chat_id = message.migrate_to_chat_id
    
    if new_chat_id:
        try:
            from database import migrate_chat_id
            migrate_chat_id(old_chat_id, new_chat_id)
            logger.info(f"Migrated chat from {old_chat_id} to {new_chat_id}")
        except Exception as e:
            logger.error(f"Failed to migrate chat {old_chat_id} to {new_chat_id}: {e}")
