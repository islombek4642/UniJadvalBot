from aiogram import types, Bot
from aiogram.enums import ChatMemberStatus
import logging

logger = logging.getLogger(__name__)


async def is_admin(message: types.Message) -> bool:
    """Checks if the user who sent the message is an admin in the chat."""
    if message.chat.type == "private":
        return True
    
    try:
        member = await message.chat.get_member(message.from_user.id)
        is_admin_user = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
        if not is_admin_user:
            logger.warning(f"Unauthorized access attempt by user {message.from_user.id} in chat {message.chat.id}")
        return is_admin_user
    except Exception as e:
        logger.error(f"Error checking admin status for user {message.from_user.id} in chat {message.chat.id}: {e}")
        return False


async def is_callback_admin(callback: types.CallbackQuery, bot: Bot = None) -> bool:
    """
    Checks if the user who clicked the callback button is an admin in the chat.
    
    IMPORTANT: For callbacks, callback.message.from_user is the BOT, not the user!
    We must use callback.from_user to get the actual user who clicked.
    """
    chat = callback.message.chat
    user_id = callback.from_user.id
    
    if chat.type == "private":
        return True
    
    try:
        # Use the bot instance from callback if not provided
        if bot is None:
            bot = callback.bot
        
        member = await bot.get_chat_member(chat.id, user_id)
        is_admin_user = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
        
        if not is_admin_user:
            logger.warning(f"Unauthorized callback from user {user_id} in chat {chat.id}")
        
        return is_admin_user
    except Exception as e:
        logger.error(f"Error checking admin status for callback user {user_id} in chat {chat.id}: {e}")
        return False
