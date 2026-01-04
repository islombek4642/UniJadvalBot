"""
Handlers package initialization.
Aggregates all routers and provides the main router.
"""
from aiogram import Router

# Import all routers
from handlers.start import router as start_router
from handlers.schedule import router as schedule_router
from handlers.settings import router as settings_router
from handlers.admin_panel import router as admin_panel_router
from handlers.broadcast import router as broadcast_router
from handlers.events import router as events_router


def create_main_router() -> Router:
    """Create and configure the main router with all sub-routers."""
    main_router = Router()
    
    # Include all routers in proper order
    # Order matters for handler priority
    main_router.include_router(start_router)      # /start, /cancel, contact
    main_router.include_router(schedule_router)   # /set_schedule, /set_time
    main_router.include_router(settings_router)   # /set_language, /weekend_mode, /help
    main_router.include_router(admin_panel_router) # /stats, users, groups
    main_router.include_router(broadcast_router)   # broadcast FSM
    main_router.include_router(events_router)      # chat member updates
    
    return main_router


# Create the router instance for import
router = create_main_router()
