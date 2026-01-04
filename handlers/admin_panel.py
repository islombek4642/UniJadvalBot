"""
Admin panel handlers.
Handles /stats, /test_broadcast, users list, groups list with pagination.
Bot owner only commands.
"""
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import (
    get_chat_language, get_stats, count_users, get_paginated_users,
    count_groups, get_paginated_groups
)
from constants.messages import Messages
from handlers.common import get_main_keyboard, is_bot_owner, escape_html
import os
import math
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("test_broadcast"))
async def cmd_test_broadcast(message: types.Message):
    """Force trigger broadcast for testing - bot owner only."""
    lang = get_chat_language(message.chat.id)
    
    if not is_bot_owner(message.from_user.id):
        await message.reply(Messages.get("BOT_ADMIN_ONLY", lang))
        return

    from scheduler import send_daily_schedules
    
    await message.reply(Messages.get("TEST_BROADCAST_START", lang))
    await send_daily_schedules(force=True)
    await message.reply(Messages.get("TEST_BROADCAST_DONE", lang))
    logger.info(f"Test broadcast triggered by user {message.from_user.id}")


@router.message(Command("stats"))
@router.message(F.text.in_([Messages.get("STATS_BTN", "UZ"), Messages.get("STATS_BTN", "EN")]))
async def cmd_stats(message: types.Message):
    """Show bot statistics - bot owner only."""
    lang = get_chat_language(message.chat.id)
    
    if not is_bot_owner(message.from_user.id):
        return

    stats = get_stats()
    text = Messages.get("STATS_TEXT", lang).format(
        users=stats["users"],
        active_groups=stats["active_groups"],
        total_groups=stats["total_groups"]
    )
    await message.reply(
        text,
        reply_markup=get_main_keyboard(lang, message.chat.type, message.from_user.id)
    )


@router.message(F.text.in_([Messages.get("USERS_BTN", "UZ"), Messages.get("USERS_BTN", "EN")]))
async def cmd_users_list(message: types.Message):
    """Show paginated users list - bot owner, private chat only."""
    if not is_bot_owner(message.from_user.id) or message.chat.type != "private":
        return
    await send_user_list(message, page=1)


@router.message(F.text.in_([Messages.get("GROUPS_BTN", "UZ"), Messages.get("GROUPS_BTN", "EN")]))
async def cmd_groups_list(message: types.Message):
    """Show paginated groups list - bot owner, private chat only."""
    if not is_bot_owner(message.from_user.id) or message.chat.type != "private":
        return
    await send_group_list(message, page=1)


async def send_user_list(message_or_callback, page: int):
    """Send paginated user list."""
    is_callback = isinstance(message_or_callback, types.CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback
    
    lang = get_chat_language(message.chat.id)
    limit = 10
    offset = (page - 1) * limit
    
    total = count_users()
    total_pages = max(math.ceil(total / limit), 1)
    users = get_paginated_users(limit, offset)
    
    header = Messages.get("USERS_TITLE", lang).format(page=page, total_pages=total_pages)
    lines = []
    for i, (name, phone, username) in enumerate(users, offset + 1):
        # Escape HTML for safety
        display_name = escape_html(name) if name else "Unknown"
        uname = f"@{username}" if username else "N/A"
        lines.append(f"{i}. <b>{display_name}</b> - <code>{phone}</code> (<code>{uname}</code>)")
    
    text = header + "\n".join(lines)
    if not lines:
        text += "<i>(Bo'sh / Empty)</i>"
    
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text=Messages.get("PREV_BTN", lang), callback_data=f"plist_u:{page-1}")
    if page < total_pages:
        builder.button(text=Messages.get("NEXT_BTN", lang), callback_data=f"plist_u:{page+1}")
    builder.adjust(2)
    
    if is_callback:
        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())


async def send_group_list(message_or_callback, page: int):
    """Send paginated group list."""
    is_callback = isinstance(message_or_callback, types.CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback
    
    lang = get_chat_language(message.chat.id)
    limit = 10
    offset = (page - 1) * limit
    
    total = count_groups()
    total_pages = max(math.ceil(total / limit), 1)
    groups = get_paginated_groups(limit, offset)
    
    group_list_text = ""
    for i, (chat_id, title, g_type, username) in enumerate(groups, offset + 1):
        # Escape HTML for safety
        display_title = escape_html(title) if title else "<i>Unknown/Left Group</i>"
        visibility_icon = "🌐" if g_type == "public" or username else "🔒"
        link_part = f" (<a href='https://t.me/{username}'>@{username}</a>)" if username else ""
        group_list_text += f"{i}. {visibility_icon} <b>{display_title}</b>{link_part} (ID: <code>{chat_id}</code>)\n"
    
    text = Messages.get("GROUPS_TITLE", lang).format(
        page=page,
        total_pages=total_pages
    ) + "\n" + group_list_text
    
    if not groups:
        text += "<i>(Bo'sh / Empty)</i>"
    
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text=Messages.get("PREV_BTN", lang), callback_data=f"plist_g:{page-1}")
    if page < total_pages:
        builder.button(text=Messages.get("NEXT_BTN", lang), callback_data=f"plist_g:{page+1}")
    builder.adjust(2)
    
    if is_callback:
        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("plist_"))
async def process_list_pagination(callback: types.CallbackQuery):
    """Handle pagination callbacks for user/group lists."""
    if not is_bot_owner(callback.from_user.id):
        await callback.answer()
        return
        
    parts = callback.data.split(":")
    action = parts[0]
    page = int(parts[1])
    
    if action == "plist_u":
        await send_user_list(callback, page)
    elif action == "plist_g":
        await send_group_list(callback, page)
    
    await callback.answer()
