"""
Start and registration handlers.
Handles /start, /cancel, contact sharing, and user registration.
"""
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import get_chat_language, save_user_contact, get_user
from constants.messages import Messages
from handlers.common import (
    get_main_keyboard, get_contact_keyboard, enable_user_menu
)

router = Router()


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Global cancel handler to exit any state."""
    current_state = await state.get_state()
    lang = get_chat_language(message.chat.id)
    
    if current_state is not None:
        await state.clear()
    
    await message.reply(
        Messages.get("CANCELLED", lang),
        reply_markup=get_main_keyboard(lang, message.chat.type, message.from_user.id)
    )


@router.message(Command("start"))
@router.message(F.text.in_([Messages.get("START_BTN", "UZ"), Messages.get("START_BTN", "EN")]))
async def cmd_start(message: types.Message, state: FSMContext):
    """Handle /start command and registration flow."""
    await state.clear()
    lang = get_chat_language(message.chat.id)
    
    # Registration Check (Private Chats only)
    if message.chat.type == "private":
        if not get_user(message.from_user.id):
            await message.answer(
                Messages.get("SHARE_CONTACT_PROMPT", lang),
                reply_markup=get_contact_keyboard(lang)
            )
            return
        else:
            # Ensure menu is enabled for returning users
            await enable_user_menu(message.bot, message.from_user.id, lang)

    await message.answer(
        Messages.get("WELCOME_ADMIN", lang),
        reply_markup=get_main_keyboard(lang, message.chat.type, message.from_user.id)
    )


@router.message(F.contact)
async def process_contact(message: types.Message):
    """Handle shared contact for user registration."""
    lang = get_chat_language(message.chat.id)
    contact = message.contact
    
    # Verify the contact belongs to the user (security check)
    if contact.user_id != message.from_user.id:
        return

    save_user_contact(
        user_id=contact.user_id,
        phone=contact.phone_number,
        first_name=contact.first_name,
        last_name=contact.last_name,
        username=message.from_user.username
    )
    
    # Enable the full command menu for this user
    await enable_user_menu(message.bot, contact.user_id, lang)
    
    await message.answer(
        Messages.get("CONTACT_SAVED", lang),
        reply_markup=get_main_keyboard(lang, message.chat.type, message.from_user.id)
    )
