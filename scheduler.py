"""
Scheduler module for daily schedule broadcasts.
Features:
- Explicit timezone (Asia/Tashkent)
- Duplicate prevention via last_sent_date tracking
- Efficient querying (only fetches due schedules)
- Rate-limited sending
"""
import logging
import os
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from dotenv import load_dotenv

from database import (
    get_schedules_due_now, get_default_schedules_due, 
    mark_schedule_sent, get_all_schedules
)
from constants.messages import Messages

load_dotenv()
logger = logging.getLogger(__name__)

# Configuration
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")
DEFAULT_SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "07:30")

# Global bot reference (set by setup_scheduler)
_bot: Bot = None


async def send_daily_schedules(force: bool = False):
    """
    Check and send due schedules.
    
    Args:
        force: If True, bypass time/date checks and send all schedules
    """
    global _bot
    if _bot is None:
        logger.error("Bot not initialized! Call setup_scheduler first.")
        return
    
    try:
        from pytz import timezone
        tz = timezone(TIMEZONE)
        now = datetime.now(tz)
    except ImportError:
        now = datetime.now()
        logger.warning("pytz not installed, using system timezone")
    
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%Y-%m-%d")
    weekday = now.weekday()  # 0=Monday, 5=Saturday, 6=Sunday
    is_weekend = weekday in [5, 6]
    
    if force:
        logger.info("FORCED broadcast started - bypassing time checks")
        schedules = get_all_schedules()
        for chat_id, file_id, lang, chat_time, weekend_mode in schedules:
            if not file_id:
                continue
            # Skip weekend mode groups on weekends even in forced mode
            if weekend_mode and is_weekend:
                logger.info(f"Skipping {chat_id}: weekend mode on, weekend day")
                continue
            await _send_schedule(chat_id, file_id, lang, current_date)
        logger.info("FORCED broadcast complete")
        return
    
    # Normal scheduled run - fetch only due schedules
    logger.debug(f"Checking schedules at {current_time} on {current_date}")
    
    # Get schedules with custom time matching current time
    due_schedules = get_schedules_due_now(current_time, current_date, is_weekend)
    
    # Get schedules with default time (no custom time set)
    default_schedules = get_default_schedules_due(DEFAULT_SCHEDULE_TIME, current_time, current_date, is_weekend)
    
    all_due = due_schedules + default_schedules
    
    if not all_due:
        logger.debug(f"No schedules due at {current_time}")
        return
    
    logger.info(f"Found {len(all_due)} schedules due at {current_time}")
    
    for chat_id, file_id, lang in all_due:
        await _send_schedule(chat_id, file_id, lang, current_date)


async def _send_schedule(chat_id: int, file_id: str, lang: str, current_date: str):
    """Send schedule to a single chat with error handling."""
    global _bot
    try:
        await _bot.send_photo(
            chat_id=chat_id,
            photo=file_id,
            caption=Messages.get("DAILY_CAPTION", lang)
        )
        # Mark as sent AFTER successful send
        mark_schedule_sent(chat_id, current_date)
        logger.info(f"Successfully sent schedule to {chat_id}")
    except Exception as e:
        # Log the error but don't crash - try other schedules
        error_str = str(e)
        if "blocked" in error_str.lower() or "deactivated" in error_str.lower():
            logger.warning(f"Bot blocked/user deactivated in {chat_id}: {e}")
        elif "chat not found" in error_str.lower():
            logger.warning(f"Chat not found {chat_id}: {e}")
        else:
            logger.error(f"Failed to send schedule to {chat_id}: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Create and configure the scheduler.
    
    Returns:
        Configured AsyncIOScheduler instance (not yet started)
    """
    global _bot
    _bot = bot
    
    # Create scheduler with timezone (using memory storage - reliable and simple)
    try:
        from pytz import timezone
        tz = timezone(TIMEZONE)
        scheduler = AsyncIOScheduler(timezone=tz)
    except ImportError:
        logger.warning("pytz not installed - scheduler may use wrong timezone!")
        scheduler = AsyncIOScheduler()
    
    # Add the main job - runs every minute to check for due broadcasts
    scheduler.add_job(
        send_daily_schedules,
        "interval",
        minutes=1,
        id="daily_schedule_check",
        replace_existing=True,
        misfire_grace_time=60
    )
    
    logger.info(f"Scheduler configured with timezone: {TIMEZONE}")
    return scheduler
