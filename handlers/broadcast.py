"""
Broadcast handlers.
Handles broadcast FSM with rate limiting for mass messaging.
"""
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database import (
    get_chat_language, get_stats, get_all_schedules, get_all_user_ids
)
from constants.messages import Messages
from handlers.common import BroadcastStates, get_main_keyboard, is_bot_owner
import asyncio
import logging

logger = logging.getLogger(__name__)
router = Router()

# Rate limiting configuration
BROADCAST_BATCH_SIZE = 25  # Send 25 messages per batch
BROADCAST_BATCH_DELAY = 1.0  # Wait 1 second between batches (25 msg/sec = safe for Telegram)


@router.message(F.text.in_([Messages.get("BROADCAST_BTN", "UZ"), Messages.get("BROADCAST_BTN", "EN")]))
async def cmd_broadcast(message: types.Message, state: FSMContext):
    """Start broadcast flow - bot owner, private chat only."""
    if not is_bot_owner(message.from_user.id) or message.chat.type != "private":
        return
        
    lang = get_chat_language(message.chat.id)
    await message.answer(Messages.get("BROADCAST_PROMPT", lang))
    await state.set_state(BroadcastStates.waiting_for_message)


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    """Store broadcast message and ask for confirmation."""
    lang = get_chat_language(message.chat.id)
    
    # Store message content to reuse
    await state.update_data(broadcast_message=message)

    stats = get_stats()
    # Fix: use correct key names from get_stats()
    user_count = stats.get("users", 0)
    group_count = stats.get("active_groups", 0)
    
    confirm_text = Messages.get("BROADCAST_CONFIRM", lang).format(
        users=user_count, 
        groups=group_count
    )
    
    # Simple yes/no keyboard
    kb = ReplyKeyboardBuilder()
    kb.button(text="✅ Ha" if lang == "UZ" else "✅ Yes")
    kb.button(text="❌ Yo'q" if lang == "UZ" else "❌ No")
    kb.adjust(2)
    
    await message.answer(confirm_text, reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(BroadcastStates.waiting_for_confirmation)


@router.message(BroadcastStates.waiting_for_confirmation)
async def process_broadcast_confirm(message: types.Message, state: FSMContext, bot: Bot):
    """Execute broadcast with rate limiting."""
    lang = get_chat_language(message.chat.id)
    
    # Check confirmation
    confirm_words = ["ha", "yes", "✅ ha", "✅ yes"]
    if message.text.lower() not in confirm_words:
        await message.answer(
            Messages.get("CANCELLED", lang),
            reply_markup=get_main_keyboard(lang, message.chat.type, message.from_user.id)
        )
        await state.clear()
        return

    data = await state.get_data()
    broadcast_msg = data.get("broadcast_message")
    
    if not broadcast_msg:
        await state.clear()
        return

    await message.answer(
        Messages.get("BROADCAST_STARTED", lang),
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Fetch all targets
    all_schedules = get_all_schedules()
    groups = [s[0] for s in all_schedules]  # chat_id is index 0
    users = get_all_user_ids()
    
    # Combine all targets
    all_targets = [(gid, True) for gid in groups] + [(uid, False) for uid in users]
    
    sent_groups = 0
    sent_users = 0
    errors = 0
    
    # Batch processing with rate limiting
    for i in range(0, len(all_targets), BROADCAST_BATCH_SIZE):
        batch = all_targets[i:i + BROADCAST_BATCH_SIZE]
        
        for chat_id, is_group in batch:
            try:
                await broadcast_msg.send_copy(chat_id=chat_id)
                if is_group:
                    sent_groups += 1
                else:
                    sent_users += 1
            except Exception as e:
                errors += 1
                logger.warning(f"Broadcast error for {chat_id}: {e}")
        
        # Rate limit delay between batches (if not last batch)
        if i + BROADCAST_BATCH_SIZE < len(all_targets):
            await asyncio.sleep(BROADCAST_BATCH_DELAY)
    
    await message.answer(
        Messages.get("BROADCAST_DONE", lang).format(
            users=sent_users,
            groups=sent_groups,
            errors=errors
        ),
        reply_markup=get_main_keyboard(lang, message.chat.type, message.from_user.id)
    )
    await state.clear()
    logger.info(f"Broadcast complete: {sent_users} users, {sent_groups} groups, {errors} errors")
