from aiogram import Router, types, F, Bot
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from utils.admin_check import is_admin
from database import (
    save_schedule, get_chat_language, set_chat_language, 
    get_all_schedules, save_user_contact, get_user, get_schedule, set_chat_time, get_stats,
    count_users, get_paginated_users, count_groups, get_paginated_groups,
    toggle_weekend_mode, get_weekend_mode, delete_schedule, get_all_user_ids,
    register_group
)
from constants.messages import Messages
import os
import re
import math
import asyncio

router = Router()

class ScheduleStates(StatesGroup):
    waiting_for_image = State()
    waiting_for_time = State()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()

def get_main_keyboard(lang: str, chat_type: str = "private", user_id: int = None):
    if chat_type != "private":
        return ReplyKeyboardRemove()
        
    builder = ReplyKeyboardBuilder()
    builder.button(text=Messages.get("SET_LANGUAGE_BTN", lang))
    builder.button(text=Messages.get("ADD_TO_GROUP_BTN", lang))
    builder.button(text=Messages.get("HELP_BTN", lang))
    
    # Add Admin buttons for bot owner
    if user_id and str(user_id) == os.getenv("ADMIN_ID"):
        builder.button(text=Messages.get("STATS_BTN", lang))
        builder.button(text=Messages.get("USERS_BTN", lang))
        builder.button(text=Messages.get("GROUPS_BTN", lang))
        builder.button(text=Messages.get("BROADCAST_BTN", lang))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True, selective=True)

def get_contact_keyboard(lang: str):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=Messages.get("SHARE_CONTACT_BTN", lang), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

async def enable_user_menu(bot: Bot, user_id: int, lang: str):
    """Enable the full command menu for a specific user after registration."""
    commands = [
        types.BotCommand(command="start", description="Botni ishga tushirish / Start the bot"),
        types.BotCommand(command="set_language", description="Tilni tanlash / Select language"),
        types.BotCommand(command="help", description="Yordam / Help")
    ]
    await bot.set_my_commands(commands, scope=types.BotCommandScopeChat(chat_id=user_id))

    await bot.set_my_commands(commands, scope=types.BotCommandScopeChat(chat_id=user_id))

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Global cancel handler to exit any state"""
    current_state = await state.get_state()
    if current_state is None:
        await message.reply(
            Messages.get("CANCELLED", get_chat_language(message.chat.id)), 
            reply_markup=get_main_keyboard(get_chat_language(message.chat.id), message.chat.type, message.from_user.id)
        )
        return

    await state.clear()
    lang = get_chat_language(message.chat.id)
    await message.reply(
        Messages.get("CANCELLED", lang),
        reply_markup=get_main_keyboard(lang, message.chat.type, message.from_user.id)
    )

@router.message(Command("start"))
@router.message(F.text.in_([Messages.get("START_BTN", "UZ"), Messages.get("START_BTN", "EN")]))
async def cmd_start(message: types.Message, state: FSMContext):
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
    lang = get_chat_language(message.chat.id)
    contact = message.contact
    
    # Verify the contact belongs to the user
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

@router.message(Command("help"))
@router.message(F.text.in_([Messages.get("HELP_BTN", "UZ"), Messages.get("HELP_BTN", "EN")]))
async def cmd_help(message: types.Message, state: FSMContext):
    lang = get_chat_language(message.chat.id)
    
    if message.chat.type == "private" and not get_user(message.from_user.id):
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
    lang = get_chat_language(message.chat.id)
    
    if message.chat.type == "private" and not get_user(message.from_user.id):
        await cmd_start(message, state)
        return
        
    if not await is_admin(message):
        await message.reply(Messages.get("ONLY_ADMINS", lang))
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha", callback_data="lang_UZ")
    builder.button(text="🇺🇸 English", callback_data="lang_EN")
    builder.adjust(2)

    await message.reply(
        Messages.get("CHOOSE_LANGUAGE", lang),
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("lang_"))
async def process_language_choice(callback: types.CallbackQuery):
    if not await is_admin(callback.message):
        lang = get_chat_language(callback.message.chat.id)
        await callback.answer(Messages.get("ONLY_ADMINS", lang), show_alert=True)
        return

    new_lang = callback.data.split("_")[1]
    set_chat_language(callback.message.chat.id, new_lang)
    
    await callback.message.edit_text(
        Messages.get("LANGUAGE_SET", new_lang),
        reply_markup=None
    )
    # Refresh only if in private chat
    if callback.message.chat.type == "private":
        await callback.message.answer(
            Messages.get("WELCOME_ADMIN", new_lang),
            reply_markup=get_main_keyboard(new_lang, callback.message.chat.type, callback.from_user.id)
        )
    await callback.answer()

@router.message(Command("set_schedule"))
@router.message(F.text.in_([Messages.get("SET_SCHEDULE_BTN", "UZ"), Messages.get("SET_SCHEDULE_BTN", "EN")]))
async def cmd_set_schedule(message: types.Message, state: FSMContext):
    lang = get_chat_language(message.chat.id)
    
    if message.chat.type == "private":
        await message.reply(Messages.get("GROUPS_ONLY", lang))
        return

    if not await is_admin(message):
        await message.reply(Messages.get("ONLY_ADMINS", lang))
        return

    await state.set_state(ScheduleStates.waiting_for_image)
    # Always remove keyboard when entering state
    await message.reply(
        Messages.get("PROMPT_IMAGE", lang),
        reply_markup=types.ReplyKeyboardRemove()
    )

@router.message(ScheduleStates.waiting_for_image, F.photo)
async def process_schedule_image(message: types.Message, state: FSMContext):
    lang = get_chat_language(message.chat.id)
    file_id = message.photo[-1].file_id
    chat_id = message.chat.id
    
    save_schedule(chat_id, file_id)
    await state.clear()
    
    # Get scheduled time for notification
    schedule_time = os.getenv("SCHEDULE_TIME", "07:30")
    
    kb = get_main_keyboard(lang, message.chat.type, message.from_user.id) if message.chat.type == "private" else types.ReplyKeyboardRemove()
    await message.reply(
        Messages.get("SCHEDULE_SAVED", lang).format(time=schedule_time),
        reply_markup=kb
    )

@router.message(Command("test_broadcast"))
async def cmd_test_broadcast(message: types.Message):
    lang = get_chat_language(message.chat.id)
    # Global Admin Restriction (Bot Owner only)
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        await message.reply(Messages.get("BOT_ADMIN_ONLY", lang))
        return

    from scheduler import send_daily_schedules
    
    await message.reply(Messages.get("TEST_BROADCAST_START", lang))
    await send_daily_schedules(message.bot, force=True)
    await message.reply(Messages.get("TEST_BROADCAST_DONE", lang))

@router.message(Command("stats"))
@router.message(F.text.in_([Messages.get("STATS_BTN", "UZ"), Messages.get("STATS_BTN", "EN")]))
async def cmd_stats(message: types.Message):
    lang = get_chat_language(message.chat.id)
    # Restriction (Bot Owner only)
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        return

    stats = get_stats()
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
    if str(message.from_user.id) != os.getenv("ADMIN_ID") or message.chat.type != "private":
        return
    await send_user_list(message, page=1)

@router.message(F.text.in_([Messages.get("GROUPS_BTN", "UZ"), Messages.get("GROUPS_BTN", "EN")]))
async def cmd_groups_list(message: types.Message):
    if str(message.from_user.id) != os.getenv("ADMIN_ID") or message.chat.type != "private":
        return
    await send_group_list(message, page=1)

async def send_user_list(message: types.Message, page: int):
    lang = get_chat_language(message.chat.id)
    limit = 10
    offset = (page - 1) * limit
    
    total = count_users()
    total_pages = max(math.ceil(total / limit), 1)
    users = get_paginated_users(limit, offset)
    
    header = Messages.get("USERS_TITLE", lang).format(page=page, total_pages=total_pages)
    lines = []
    for i, (name, phone, username) in enumerate(users, offset + 1):
        # Escape HTML for safety and handle underscores
        display_name = name.replace("<", "&lt;").replace(">", "&gt;")
        uname = f"@{username}" if username else "N/A"
        # Using code blocks for phone and username to preserve underscores and allow easy copying
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
    
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

async def send_group_list(message: types.Message, page: int):
    lang = get_chat_language(message.chat.id)
    limit = 10
    offset = (page - 1) * limit
    
    total = count_groups()
    total_pages = max(math.ceil(total / limit), 1)
    groups = get_paginated_groups(limit, offset) # groups is now list of tuples (chat_id, title, type, username)
    
    group_list_text = ""
    for i, (chat_id, title, g_type, username) in enumerate(groups, offset + 1):
        # Escape HTML for safety
        display_title = title.replace("<", "&lt;").replace(">", "&gt;") if title else "<i>Unknown/Left Group</i>"
        visibility_icon = "🌐" if g_type == "public" or username else "🔒"
        link_part = f" (<a href='https://t.me/{username}'>@{username}</a>)" if username else ""
        group_list_text += f"{i}. {visibility_icon} <b>{display_title}</b>{link_part} (ID: <code>{chat_id}</code>)\n"
    
    text = Messages.get("GROUPS_TITLE", lang).format(
        page=page,
        total_pages=total_pages
    ) + "\n" + group_list_text
    
    if not groups: # Check if the list of groups is empty
        text += "<i>(Bo'sh / Empty)</i>"
    
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text=Messages.get("PREV_BTN", lang), callback_data=f"plist_g:{page-1}")
    if page < total_pages:
        builder.button(text=Messages.get("NEXT_BTN", lang), callback_data=f"plist_g:{page+1}")
    builder.adjust(2)
    
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("plist_"))
async def process_list_pagination(callback: types.CallbackQuery):
    if str(callback.from_user.id) != os.getenv("ADMIN_ID"):
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

@router.message(Command("weekend_mode"))
async def cmd_toggle_weekend_mode(message: types.Message):
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

@router.my_chat_member()
async def on_my_chat_member_update(update: types.ChatMemberUpdated, bot: Bot):
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
                # We can't know the language of the group for sure if it's not saved, 
                # but we can try to get it or default to UZ
                lang = get_chat_language(chat_id) or "UZ"
                
                # Fetch more details for notification
                username =  update.chat.username
                chat_type_raw = update.chat.type
                
                # Determine Public/Private based on username presence
                vis_type = "public" if username else "private"
                type_icon = "🌐" if vis_type == "public" else "�"
                
                # Format username link
                username_link = f"<a href='https://t.me/{username}'>@{username}</a>" if username else ""
                
                total_groups = count_groups()
                await bot.send_message(
                    chat_id=admin_id,
                    text=Messages.get("BOT_KICKED", lang).format(
                        title=title, 
                        chat_id=chat_id, 
                        total_groups=total_groups,
                        type_icon=type_icon,
                        username_link=username_link
                    )
                )
            except Exception as e:
                logger.error(f"Failed to notify admin about removal from {chat_id}: {e}")

    # Detect if bot joined a new group
    elif update.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        # Only notify if it wasn't already a member (e.g. permission change)
        if update.old_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.RESTRICTED]:
            chat_id = update.chat.id
            title = update.chat.title or "Unknown"
            chat_type_raw = update.chat.type
            username = update.chat.username
            
            # Determine Public/Private
            vis_type = "public" if username else "private"
            
            # Register group in DB immediately with new type logic
            register_group(chat_id, title, vis_type, username)
            
            # Notify bot owner
            admin_id = os.getenv("ADMIN_ID")
            if admin_id:
                try:
                    count = await bot.get_chat_member_count(chat_id)
                    total_groups = count_groups()
                    
                    # Format type icon
                    type_icon = "🌐" if vis_type == "public" else "�"
                    
                    # Format username link
                    username_link = f"<a href='https://t.me/{username}'>@{username}</a>" if username else ""

                    # For notification, we use default admin language or UZ
                    # Since we don't know the admin's preference here easily, we pick UZ or EN based on general context
                    # But better to use the language of the admin if it was possible. 
                    # Here we default to UZ as it acts as a system log.
                    await bot.send_message(
                        chat_id=admin_id,
                        text=Messages.get("BOT_ADDED", "UZ").format(
                            title=title, 
                            chat_id=chat_id, 
                            count=count, 
                            total_groups=total_groups,
                            type_icon=type_icon,
                            username_link=username_link
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin about new group {chat_id}: {e}")

@router.message(F.text.in_([Messages.get("ADD_TO_GROUP_BTN", "UZ"), Messages.get("ADD_TO_GROUP_BTN", "EN")]))
async def cmd_invite_bot(message: types.Message, bot: Bot):
    lang = get_chat_language(message.chat.id)
    bot_info = await bot.get_me()
    
    # Deep link to add bot to group as admin with required permissions
    # permissions: post_messages, edit_messages, delete_messages, invite_users
    invite_url = f"https://t.me/{bot_info.username}?startgroup=true&admin=post_messages+edit_messages+delete_messages+invite_users"
    
    builder = InlineKeyboardBuilder()
    builder.button(text=Messages.get("ADD_TO_GROUP_BTN", lang), url=invite_url)
    
    await message.answer(
        Messages.get("INVITE_PROMPT", lang),
        reply_markup=builder.as_markup()
    )

@router.message(Command("set_time"))
async def cmd_set_time(message: types.Message, state: FSMContext):
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

@router.message(ScheduleStates.waiting_for_time)
async def process_set_time(message: types.Message, state: FSMContext):
    lang = get_chat_language(message.chat.id)
    time_str = message.text.strip()
    
    if not re.match(r"^([01][0-9]|2[0-3]):[0-5][0-9]$", time_str):
        await message.reply(Messages.get("INVALID_TIME_FORMAT", lang))
        return

    set_chat_time(message.chat.id, time_str)
    await state.clear()
    await message.reply(Messages.get("TIME_UPDATED", lang).format(time=time_str))

@router.message(ScheduleStates.waiting_for_image, Command("cancel"))
@router.message(ScheduleStates.waiting_for_time, Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    lang = get_chat_language(message.chat.id)
    await state.clear()
    await message.reply(
        Messages.get("CANCELLED", lang),
        reply_markup=get_main_keyboard(lang, message.chat.type, message.from_user.id)
    )

@router.message(ScheduleStates.waiting_for_image)
async def process_not_image(message: types.Message):
    lang = get_chat_language(message.chat.id)
    await message.reply(Messages.get("INVALID_IMAGE", lang))

@router.message(F.text.in_([Messages.get("BROADCAST_BTN", "UZ"), Messages.get("BROADCAST_BTN", "EN")]))
async def cmd_broadcast(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != os.getenv("ADMIN_ID") or message.chat.type != "private":
        return
        
    lang = get_chat_language(message.chat.id)
    await message.answer(Messages.get("BROADCAST_PROMPT", lang))
    await state.set_state(BroadcastStates.waiting_for_message)

@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    lang = get_chat_language(message.chat.id)
    
    # Store message content (text or photo+caption) to reuse
    await state.update_data(broadcast_message=message)

    stats = get_stats()
    confirm_text = Messages.get("BROADCAST_CONFIRM", lang).format(
        users=stats["users"], 
        groups=stats["groups"]
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
    lang = get_chat_language(message.chat.id)
    
    if message.text.lower() not in ["ha", "yes", "✅ ha", "✅ yes"]:
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
    
    # Get all targets
    # For simplicity, we just fetch IDs again. In a large scale app, iterate with cursor.
    # We need to fetch all user IDs and group IDs. database.py needs update for getAllUserIds
    # For now, reusing paginated functions iteratively or just fetching all if functions added.
    # Let's assume database functions return list of all active IDs or iterate locally.
    # Since get_paginated_users takes limit/offset, to broadcast we need ALL.
    # Let's add a quick helper below or use get_all_schedules (groups) + something for users.
    
    # Fetch all group IDs
    all_schedules = get_all_schedules()
    groups = [s[0] for s in all_schedules] # chat_id is index 0
    
    # Fetch all user IDs
    users = get_all_user_ids()
    
    sent_groups = 0
    sent_users = 0
    errors = 0
    
    async def send_to_chat(chat_id, is_group=True):
        nonlocal sent_groups, sent_users, errors
        try:
            # Copy the message to the target chat
            await broadcast_msg.send_copy(chat_id=chat_id)
            if is_group:
                sent_groups += 1
            else:
                sent_users += 1
        except Exception as e:
            errors += 1
            # logger.error(f"Broadcast error for {chat_id}: {e}")
            pass

    # Process groups and users
    # We combine them to run in parallel but be careful with limits if volume is huge
    # For < 5000 users this is fine. For larger, batching is needed.
    tasks = [send_to_chat(gid, True) for gid in groups] + [send_to_chat(uid, False) for uid in users]
    
    if tasks:
        await asyncio.gather(*tasks)
    
    await message.answer(
        Messages.get("BROADCAST_DONE", lang).format(
            users=sent_users,
            groups=sent_groups,
            errors=errors
        ),
        reply_markup=get_main_keyboard(lang, message.chat.type, message.from_user.id)
    )
    await state.clear()

@router.message()
async def catch_all(message: types.Message):
    # Ignore random text messages
    pass
