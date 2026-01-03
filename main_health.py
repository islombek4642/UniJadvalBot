from aiohttp import web
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.admin import router as admin_router
from database import init_db
from scheduler import setup_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

load_dotenv()

async def set_commands(bot: Bot):
    private_commands = [
        types.BotCommand(command="start", description="Botni ishga tushurish / Start the bot")
    ]
    
    group_commands = [
        types.BotCommand(command="set_schedule", description="Dars jadvalini o'rnatish / Set schedule image"),
        types.BotCommand(command="set_time", description="Yuborish vaqtini sozlash / Set broadcast time"),
        types.BotCommand(command="weekend_mode", description="Dam olish kuni rejimini yoqish/o'chirish / Toggle weekend mode"),
        types.BotCommand(command="help", description="Yordam / Help")
    ]
    
    await bot.set_my_commands(private_commands, scope=types.BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(group_commands, scope=types.BotCommandScopeAllGroupChats())
    logger.info("Bot commands menu initialized with separate scopes.")

async def set_bot_profile(bot: Bot):
    description = (
        "Ushbu bot guruhlarga har kuni avtomatik ravishda dars jadvalini yuborish uchun mo'ljallangan.\n\n"
        "Asosiy imkoniyatlar:\n"
        "✅ Har bir guruh uchun alohida yuborish vaqtini sozlash\n"
        "✅ Haftalik dars jadvalini rasm shaklida yuklash\n"
        "✅ O'zbek va ingliz tillarini qo'llab-quvvatlash"
    )
    short_description = "Guruhlar uchun avtomatik dars jadvali tarqatuvchi bot."
    
    await bot.set_my_description(description=description)
    await bot.set_my_short_description(short_description=short_description)
    logger.info("Bot profile description and short description updated.")

async def health_check(request):
    """Health check endpoint for Sliplane"""
    return web.Response(text="UniJadval Bot is running! 🚀")

async def main():
    logger.info("Starting UniJadval Bot (Polling + Health Check)...")
    
    # Initialize database
    init_db()
    
    # Initialize bot and dispatcher
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN not found in .env file! Exiting...")
        sys.exit(1)

    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    # Set bot commands and profile
    await set_commands(bot)
    await set_bot_profile(bot)

    # Register routers
    dp.include_router(admin_router)

    # Setup scheduler
    scheduler = setup_scheduler(bot)
    scheduler.start()

    logger.info("Bot is polling...")
    
    # Create aiohttp app for health check
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    # Start bot polling in background
    polling_task = asyncio.create_task(dp.start_polling(bot))
    
    # Start web server for health check
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
    await site.start()
    
    logger.info("Bot is running with polling and health check on port 8080")
    
    try:
        # Wait for polling to complete
        await polling_task
    except Exception as e:
        logger.error(f"An error occurred during polling: {e}")
    finally:
        logger.info("Shutting down...")
        scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt)")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
