"""
Schedule management handlers.
Handles /set_schedule, /set_time, schedule image upload FSM.
"""
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from database import (
    get_chat_language, save_schedule, get_schedule, set_chat_time
)
from constants.messages import Messages
from handlers.common import ScheduleStates, get_main_keyboard
from utils.admin_check import is_admin
import os
import re
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("set_schedule"))
@router.message(F.text.in_([Messages.get("SET_SCHEDULE_BTN", "UZ"), Messages.get("SET_SCHEDULE_BTN", "EN")]))
async def cmd_set_schedule(message: types.Message, state: FSMContext):
    """Start schedule upload flow - groups only, admin only."""
    lang = get_chat_language(message.chat.id)
    
    if message.chat.type == "private":
        await message.reply(Messages.get("GROUPS_ONLY", lang))
        return

    if not await is_admin(message):
        await message.reply(Messages.get("ONLY_ADMINS", lang))
        return

    await state.set_state(ScheduleStates.waiting_for_image)
    # Always remove keyboard when entering state in groups
    await message.reply(
        Messages.get("PROMPT_IMAGE", lang),
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(ScheduleStates.waiting_for_image, F.photo)
async def process_schedule_image(message: types.Message, state: FSMContext):
    """Process uploaded schedule image."""
    lang = get_chat_language(message.chat.id)
    file_id = message.photo[-1].file_id  # Get highest resolution
    chat_id = message.chat.id
    
    save_schedule(chat_id, file_id)
    await state.clear()
    
    # Get scheduled time for notification
    schedule_time = os.getenv("SCHEDULE_TIME", "07:30")
    
    kb = get_main_keyboard(lang, message.chat.type, message.from_user.id) if message.chat.type == "private" else ReplyKeyboardRemove()
    await message.reply(
        Messages.get("SCHEDULE_SAVED", lang).format(time=schedule_time),
        reply_markup=kb
    )
    logger.info(f"Schedule saved for chat {chat_id}")


@router.message(ScheduleStates.waiting_for_image)
async def process_not_image(message: types.Message):
    """Handle non-image messages during schedule upload."""
    lang = get_chat_language(message.chat.id)
    await message.reply(Messages.get("INVALID_IMAGE", lang))


@router.message(Command("set_time"))
async def cmd_set_time(message: types.Message, state: FSMContext):
    """Set custom broadcast time for this group."""
    lang = get_chat_language(message.chat.id)

    if message.chat.type == "private":
        await message.reply(Messages.get("GROUPS_ONLY", lang))
        return

    if not await is_admin(message):
        await message.reply(Messages.get("ONLY_ADMINS", lang))
        return

    # Check if schedule exists first
    if not get_schedule(message.chat.id):
        await message.reply(Messages.get("SCHEDULE_NEEDED", lang))
        return

    args = message.text.split()
    if len(args) < 2:
        await state.set_state(ScheduleStates.waiting_for_time)
        await message.reply(Messages.get("SET_TIME_PROMPT", lang))
        return

    time_str = args[1]
    if not re.match(r"^([01][0-9]|2[0-3]):[0-5][0-9]$", time_str):
        await message.reply(Messages.get("INVALID_TIME_FORMAT", lang))
        return

    set_chat_time(message.chat.id, time_str)
    await message.reply(Messages.get("TIME_UPDATED", lang).format(time=time_str))
    logger.info(f"Broadcast time set to {time_str} for chat {message.chat.id}")


@router.message(ScheduleStates.waiting_for_time)
async def process_set_time(message: types.Message, state: FSMContext):
    """Process time input during set_time flow."""
    lang = get_chat_language(message.chat.id)
    time_str = message.text.strip()
    
    if not re.match(r"^([01][0-9]|2[0-3]):[0-5][0-9]$", time_str):
        await message.reply(Messages.get("INVALID_TIME_FORMAT", lang))
        return

    set_chat_time(message.chat.id, time_str)
    await state.clear()
    await message.reply(Messages.get("TIME_UPDATED", lang).format(time=time_str))
    logger.info(f"Broadcast time set to {time_str} for chat {message.chat.id}")
