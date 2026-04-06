"""Module that handles endpoints for anytype automation."""

from functools import lru_cache

from fastapi import APIRouter

from utils.logger import logger

from services.anytype.core_service import AnytypeService
from services.anytype.journal_service import JournalService
from services.anytype.space_service import SpaceService
from services.anytype.task_service import TaskService

from models.anytype_models import SpaceEditRequest

from settings import generate_settings

settings = generate_settings()


@lru_cache
def get_space_service():
    return SpaceService(settings)


@lru_cache
def get_task_service():
    return TaskService(
        settings, get_journal_service() if settings.config.journal_space_id else None
    )


@lru_cache
def get_journal_service():
    return JournalService(settings)


router = APIRouter()

settings = generate_settings()
anytype_spaces = get_space_service()
anytype_tasks = get_task_service()
anytype_automation = AnytypeService(settings, anytype_tasks, anytype_spaces)
anytype_journal = get_journal_service()


@router.get("/recurrent_check", tags=["scheduled", "tasks"])
async def recurrent_check():
    """Endpoint for task maintenance"""
    logger.info("Recurrent check endpoint called")
    return anytype_tasks.recurrent_check()


@router.get("/scan_space/{space_name}/id/{space_id}", tags=["spaces", "general"])
async def scan_space(space_name, space_id):
    """Endpoint to populate Data with space data"""
    logger.info("Space scanner endpoint called")
    return anytype_spaces.scan_space(space_name, space_id)


@router.post("/migrate", tags=["spaces"])
async def migrate(edit_request: SpaceEditRequest):
    """Endpoint for copying types and their from one space to another"""
    logger.info("Migration Endpoint called")
    return anytype_spaces.migrate_spaces(edit_request)


@router.post("/sync_spaces", tags=["spaces"])
async def scan_spaces(sync_request: SpaceEditRequest):
    """Endpoint for scanning spaces for altering configuration file"""
    logger.info("Space syncer endpoint called")
    return anytype_automation.sync_spaces(sync_request)


@router.get("/daily_rollover", tags=["scheduled"])
async def task_status_reset():
    """Endpoint to update overdue or no collection tasks"""
    logger.info("Daily rollover endpoint called")
    return anytype_automation.daily_rollover()


if settings.config.journal_space_id:

    @router.get("/day_journal", tags=["scheduled", "journal"])
    async def day_journal():
        """Endpoint to fetch or create day journal instance id"""
        logger.info("Day Journal endpoint called")
        return anytype_journal.find_or_create_day_journal()

    @router.get("/log_habit/{object_id}", tags=["journal"])
    async def log_habit(object_id):
        """Endpoint to Log Habit occurrences"""
        logger.info("Log Habit endpoint called")
        return anytype_journal.log_habit(object_id)
