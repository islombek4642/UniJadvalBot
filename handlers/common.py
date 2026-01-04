"""
Common utilities shared across all handlers.
Contains FSM states, keyboard builders, and utility functions.
"""
from aiogram import types, Bot
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from constants.messages import Messages
from database import get_chat_language
import os
import logging

logger = logging.getLogger(__name__)


# ============ FSM States ============

class ScheduleStates(StatesGroup):
    """States for schedule upload flow"""
    waiting_for_image = State()
    waiting_for_time = State()


class BroadcastStates(StatesGroup):
    """States for broadcast message flow"""
    waiting_for_message = State()
    waiting_for_confirmation = State()


# ============ Keyboard Builders ============

def get_main_keyboard(lang: str, chat_type: str = "private", user_id: int = None):
    """
    Returns the main reply keyboard for private chats.
    In groups, returns ReplyKeyboardRemove to avoid sticky keyboards.
    """
    if chat_type != "private":
        return ReplyKeyboardRemove()
        
    builder = ReplyKeyboardBuilder()
    builder.button(text=Messages.get("SET_LANGUAGE_BTN", lang))
    builder.button(text=Messages.get("ADD_TO_GROUP_BTN", lang))
    builder.button(text=Messages.get("HELP_BTN", lang))
    
    # Add Admin buttons for bot owner
    admin_id = os.getenv("ADMIN_ID")
    if user_id and admin_id and str(user_id) == admin_id:
        builder.button(text=Messages.get("STATS_BTN", lang))
        builder.button(text=Messages.get("USERS_BTN", lang))
        builder.button(text=Messages.get("GROUPS_BTN", lang))
        builder.button(text=Messages.get("BROADCAST_BTN", lang))
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True, selective=True)


def get_contact_keyboard(lang: str):
    """Returns keyboard with contact sharing button for registration."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=Messages.get("SHARE_CONTACT_BTN", lang), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def get_language_keyboard():
    """Returns inline keyboard for language selection."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha", callback_data="lang_UZ")
    builder.button(text="🇺🇸 English", callback_data="lang_EN")
    builder.adjust(2)
    return builder.as_markup()


# ============ Utility Functions ============

async def enable_user_menu(bot: Bot, user_id: int, lang: str):
    """Enable the full command menu for a specific user after registration."""
    commands = [
        types.BotCommand(command="start", description="Botni ishga tushirish / Start the bot"),
        types.BotCommand(command="set_language", description="Tilni tanlash / Select language"),
        types.BotCommand(command="help", description="Yordam / Help")
    ]
    try:
        await bot.set_my_commands(commands, scope=types.BotCommandScopeChat(chat_id=user_id))
        logger.info(f"Enabled user menu for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to set user menu for {user_id}: {e}")


def is_bot_owner(user_id: int) -> bool:
    """Check if user is the bot owner (ADMIN_ID from .env)."""
    admin_id = os.getenv("ADMIN_ID")
    return admin_id and str(user_id) == admin_id


def escape_html(text: str) -> str:
    """Escape HTML special characters to prevent injection."""
    if not text:
        return ""
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
