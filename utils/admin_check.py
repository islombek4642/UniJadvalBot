from aiogram import types
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
