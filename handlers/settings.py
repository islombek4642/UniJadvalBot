"""
Settings handlers.
Handles /set_language, /weekend_mode, /help, language callback, and invite.
"""
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import (
    get_chat_language, set_chat_language, get_user,
    toggle_weekend_mode
)
from constants.messages import Messages
from handlers.common import get_main_keyboard, get_language_keyboard
from utils.admin_check import is_admin, is_callback_admin
import os
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("help"))
@router.message(F.text.in_([Messages.get("HELP_BTN", "UZ"), Messages.get("HELP_BTN", "EN")]))
async def cmd_help(message: types.Message, state: FSMContext):
    """Show help information with admin contact button."""
    lang = get_chat_language(message.chat.id)
    
    # Redirect unregistered private users to /start
    if message.chat.type == "private" and not get_user(message.from_user.id):
        from handlers.start import cmd_start
        await cmd_start(message, state)
        return
        
    admin_id = os.getenv("ADMIN_ID", "")
    schedule_time = os.getenv("SCHEDULE_TIME", "07:30")
    
    builder = InlineKeyboardBuilder()
    if admin_id:
        builder.button(text=Messages.get("CONTACT_ADMIN_BTN", lang), url=f"tg://user?id={admin_id}")
    
    await message.reply(
        Messages.get("HELP_TEXT", lang).format(time=schedule_time),
        reply_markup=builder.as_markup()
    )


@router.message(Command("set_language"))
@router.message(F.text.in_([Messages.get("SET_LANGUAGE_BTN", "UZ"), Messages.get("SET_LANGUAGE_BTN", "EN")]))
async def cmd_set_language(message: types.Message, state: FSMContext):
    """Show language selection buttons."""
    lang = get_chat_language(message.chat.id)
    
    # Redirect unregistered private users to /start
    if message.chat.type == "private" and not get_user(message.from_user.id):
        from handlers.start import cmd_start
        await cmd_start(message, state)
        return
        
    if not await is_admin(message):
        await message.reply(Messages.get("ONLY_ADMINS", lang))
        return

    await message.reply(
        Messages.get("CHOOSE_LANGUAGE", lang),
        reply_markup=get_language_keyboard()
    )


@router.callback_query(F.data.startswith("lang_"))
async def process_language_choice(callback: types.CallbackQuery):
    """Handle language selection callback."""
    # Use is_callback_admin which correctly checks callback.from_user
    if not await is_callback_admin(callback):
        lang = get_chat_language(callback.message.chat.id)
        await callback.answer(Messages.get("ONLY_ADMINS", lang), show_alert=True)
        return

    new_lang = callback.data.split("_")[1]
    set_chat_language(callback.message.chat.id, new_lang)
    
    await callback.message.edit_text(
        Messages.get("LANGUAGE_SET", new_lang),
        reply_markup=None
    )
    
    # Refresh keyboard only in private chat
    if callback.message.chat.type == "private":
        await callback.message.answer(
            Messages.get("WELCOME_ADMIN", new_lang),
            reply_markup=get_main_keyboard(new_lang, callback.message.chat.type, callback.from_user.id)
        )
    
    await callback.answer()
    logger.info(f"Language set to {new_lang} for chat {callback.message.chat.id}")


@router.message(Command("weekend_mode"))
async def cmd_toggle_weekend_mode(message: types.Message):
    """Toggle weekend mode for this group."""
    lang = get_chat_language(message.chat.id)
    
    if message.chat.type == "private":
        await message.reply(Messages.get("GROUPS_ONLY", lang))
        return

    if not await is_admin(message):
        await message.reply(Messages.get("ONLY_ADMINS", lang))
        return
        
    new_val = toggle_weekend_mode(message.chat.id)
    new_status = bool(new_val)
    
    status_label = Messages.get("WEEKEND_MODE_ON" if new_status else "WEEKEND_MODE_OFF", lang)
    await message.reply(
        Messages.get("WEEKEND_MODE_UPDATED", lang).format(status=status_label)
    )
    logger.info(f"Weekend mode set to {new_status} for chat {message.chat.id}")


@router.message(F.text.in_([Messages.get("ADD_TO_GROUP_BTN", "UZ"), Messages.get("ADD_TO_GROUP_BTN", "EN")]))
async def cmd_invite_bot(message: types.Message, bot: Bot):
    """Show button to add bot to a group."""
    lang = get_chat_language(message.chat.id)
    bot_info = await bot.get_me()
    
    # Deep link to add bot to group as admin with required permissions
    invite_url = f"https://t.me/{bot_info.username}?startgroup=true&admin=post_messages+edit_messages+delete_messages+invite_users"
    
    builder = InlineKeyboardBuilder()
    builder.button(text=Messages.get("ADD_TO_GROUP_BTN", lang), url=invite_url)
    
    await message.answer(
        Messages.get("INVITE_PROMPT", lang),
        reply_markup=builder.as_markup()
    )
