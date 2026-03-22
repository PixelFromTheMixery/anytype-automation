"""Module that handles endpoints for anytype automation."""

from fastapi import APIRouter

from utils.data import DataManager
from utils.logger import logger

from services.anytype.core_service import AnytypeService
from services.anytype.journal_service import JournalService
from services.anytype.task_service import TaskService


from models.data_request import DataRequest
from models.migrate_request import MigrateRequest
from models.space_sync_request import SpaceSyncRequest
from models.search_request import SearchRequest

router = APIRouter()
anytype_automation = AnytypeService()
anytype_tasks = TaskService()
anytype_journal = JournalService()


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


@router.get("/day_journal", tags=["scheduled"])
async def day_journal():
    """Endpoint to fetch or create day journal instance id"""
    logger.info("Day Journal endpoint called")
    return anytype_journal.find_or_create_day_journal()


@router.post("/search", tags=["tools"])
async def search(search_request: SearchRequest):
    """Endpoint for searching objects"""
    logger.info("Search endpoint called")
    return anytype_automation.search(SearchRequest.model_dump(search_request))


@router.post("/sync_spaces", tags=["tools"])
async def scan_spaces(sync_request: SpaceSyncRequest):
    """Endpoint for scanning spaces for altering configuration file"""
    logger.info("Space syncer endpoint called")
    return anytype_automation.sync_spaces(SpaceSyncRequest.model_dump(sync_request))


@router.get("/scan_space/{space_name}")
async def scan_space(space_name):
    """Endpoint to populate Data with space data"""
    logger.info("Space scanner endpoint called")
    return anytype_automation.scan_space(space_name)


@router.get("/reload", tags=["tools"])
async def reload():
    """Endpoint for Reloading local DATA"""
    logger.info("Reload DATA endpoint called")
    DataManager.reload()
    return DataManager.data


@router.post("/migrate")
async def migrate(migrate_request: MigrateRequest):
    """Endpoint for copying types and their from one space to another"""
    logger.info("Migration Endpoint called")
    return anytype_automation.migrate_spaces(MigrateRequest.model_dump(migrate_request))


@router.post("/data")
async def list_types(data_request: DataRequest):
    """Endpoint for getting various data"""
    logger.info("Data fetch endpoint called")
    return anytype_automation.fetch_data(DataRequest.model_dump(data_request))


@router.post("/list_views")
async def list_views(
    space_name: str,
    query_name: str,
):
    """Endpoint to fetch automation list view"""
    logger.info("View fetcher endpoint called")
    return anytype_automation.view_list(space_name, query_name)
