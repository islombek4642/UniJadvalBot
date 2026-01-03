import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database import get_all_schedules
from constants.messages import Messages
import os

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

async def send_daily_schedules(bot: Bot, force: bool = False):
    logger.info("Starting scheduled broadcast check..." if not force else "Starting FORCED broadcast...")
    try:
        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        default_time = os.getenv("SCHEDULE_TIME", "07:30")
        
        schedules = get_all_schedules()
        logger.info(f"Checking {len(schedules)} active schedules. Time: {now}, Default: {default_time}")
        
        if not schedules:
            return

        weekday = datetime.now().weekday()  # 0=Monday, 5=Saturday, 6=Sunday

        for chat_id, file_id, lang, chat_time, weekend_mode in schedules:
            if not file_id:
                continue
                
            # Check if it's weekend and we should skip
            if weekend_mode and weekday in [5, 6] and not force:
                logger.info(f"Skipping broadcast for {chat_id}: Weekend Mode is ON")
                continue

            # Check if it's time to send
            target_time_str = chat_time if chat_time else default_time
            
            try:
                # Normalize target time
                target_time = datetime.strptime(target_time_str, "%H:%M").strftime("%H:%M")
                
                if force or target_time == now:
                    try:
                        logger.info(f"Target: {target_time}, Current: {now}, Force: {force}")
                        await bot.send_photo(
                            chat_id=chat_id,
                            photo=file_id,
                            caption=Messages.get("DAILY_CAPTION", lang)
                        )
                        logger.info(f"Success: Schedule sent to {chat_id}")
                    except Exception as e:
                        logger.error(f"Error: Failed to send schedule to {chat_id}: {e}")
                
            except Exception as e:
                logger.error(f"Error parsing target time '{target_time_str}' for chat {chat_id}: {e}")
                
    except Exception as e:
        logger.error(f"Critical error during broadcast check: {e}")

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    
    # Run every minute to check for due broadcasts
    scheduler.add_job(
        send_daily_schedules,
        "interval",
        minutes=1,
        args=[bot],
        misfire_grace_time=30  # 30 seconds grace for interval jobs
    )
    logger.info("Scheduler setup complete. Checking for due broadcasts every minute.")
    return scheduler
