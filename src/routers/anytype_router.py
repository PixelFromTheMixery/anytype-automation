"""Module that handles endpoints for anytype automation."""

from functools import lru_cache

from fastapi import APIRouter

from utils.logger import logger

from services.anytype.core_service import AnytypeService
from services.anytype.task_service import TaskService
from services.anytype.space_service import SpaceService

from models.migrate_request import MigrateRequest
from models.space_sync_request import SpaceSyncRequest

from settings import generate_settings


@lru_cache
def get_space_service():
    return SpaceService(generate_settings())


@lru_cache
def get_task_service():
    return TaskService(generate_settings())


router = APIRouter()

settings = generate_settings()
anytype_spaces = get_space_service()
anytype_tasks = get_task_service()
anytype_automation = AnytypeService(settings, anytype_tasks, anytype_spaces)


@router.get("/daily_rollover", tags=["scheduled"])
async def task_status_reset():
    """Endpoint to update overdue or no collection tasks"""
    logger.info("Daily rollover endpoint called")
    return anytype_automation.daily_rollover()


@router.get("/recurrent_check", tags=["scheduled"])
async def recurrent_check():
    """Endpoint for task maintenance"""
    logger.info("Recurrent check endpoint called")
    return anytype_tasks.recurrent_check()


@router.post("/sync_spaces", tags=["tools"])
async def scan_spaces(sync_request: SpaceSyncRequest):
    """Endpoint for scanning spaces for altering configuration file"""
    logger.info("Space syncer endpoint called")
    return anytype_automation.sync_spaces(SpaceSyncRequest.model_dump(sync_request))


@router.get("/scan_space/{space_name}/id/{space_id}")
async def scan_space(space_name, space_id):
    """Endpoint to populate Data with space data"""
    logger.info("Space scanner endpoint called")
    return anytype_spaces.scan_space(space_name, space_id)


@router.post("/migrate")
async def migrate(migrate_request: MigrateRequest):
    """Endpoint for copying types and their from one space to another"""
    logger.info("Migration Endpoint called")
    return anytype_automation.migrate_spaces(MigrateRequest.model_dump(migrate_request))
