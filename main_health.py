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
from aiohttp import web
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

load_dotenv()

async def set_commands(bot: Bot):
    # Default commands for UNREGISTERED users in private chats
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

async def handle_webhook(request):
    """Handle incoming webhook requests"""
    dispatcher = request.app['dp']
    update_data = await request.json()
    update = types.Update.model_validate(update_data, context={"bot": request.app['bot']})
    await dispatcher.feed_update(update=update)
    return web.Response(text="OK")

async def health_check(request):
    """Health check endpoint for Sliplane"""
    return web.Response(text="UniJadval Bot is running!", status=200)

async def main():
    logger.info("Starting UniJadval Bot...")
    
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
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"An error occurred during polling: {e}")
    finally:
        logger.info("Shutting down...")
        scheduler.shutdown()
        await bot.session.close()

# Web server version for platforms that need it
async def web_main():
    logger.info("Starting UniJadval Bot (Web Mode)...")
    
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

    # Create aiohttp app FIRST
    app = web.Application()
    app['dp'] = dp
    app['bot'] = bot
    
    # Add routes
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    # Start web server FIRST
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
    await site.start()
    
    logger.info(f"Web server started on port {os.getenv('PORT', 8080)}")
    logger.info("Bot is running with web server...")
    
    try:
        # Start bot polling AFTER web server
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        logger.info("Shutting down...")
        scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    # Always use web mode for Sliplane
    asyncio.run(web_main())
