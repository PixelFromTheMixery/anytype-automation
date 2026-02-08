"""Module that handles endpoints for anytype automation."""

from fastapi import APIRouter

from models.data_request import DataRequest
from models.migrate_request import MigrateRequest
from models.space_sync_request import SpaceSyncRequest
from models.search_request import SearchRequest
from services.anytype_service import AnytypeService
from utils.data import DataManager
from utils.logger import logger

router = APIRouter()
anytype_automation = AnytypeService()


@router.get("/daily_rollover", tags=["scheduled"])
async def task_status_reset():
    """Endpoint to update overdue or no collection tasks"""
    logger.info("Daily rollover endpoint called")
    return anytype_automation.daily_rollover()


@router.get("/recurrent_check", tags=["scheduled"])
async def recurrent_check():
    """Endpoint for task maintenance"""
    logger.info("Recurrent check endpoint called")
    return anytype_automation.recurrent_check()


@router.get("/day_journal", tags=["scheduled"])
async def day_journal():
    """Endpoint to fetch or create day jounal instance id"""
    logger.info("Day Journal endpoint called")
    return anytype_automation.find_or_create_day_journal()


@router.post("/search", tags=["tools"])
async def search(search_request: SearchRequest):
    """Endpoint for searching objects"""
    logger.info("Search endpoint called")
    return anytype_automation.search(SearchRequest.model_dump(search_request))


@router.post("/scan_spaces", tags=["tools"])
async def scan_spaces(sync_request: SpaceSyncRequest):
    """Endpoint for scanning spaces for altering configuration file"""
    logger.info("Space scanner endpoint called")
    return anytype_automation.scan_spaces(SpaceSyncRequest.model_dump(sync_request))


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


@router.get("/other_anytype")
async def other_endpoint():
    """Endpoint for throwaway automations"""
    logger.info("Anytype other endpoint called")
    return anytype_automation.other()


@router.get("/test_anytype")
async def test_endpoint():
    """Endpoint for throwaway tests"""
    logger.info("Anytype test endpoint called")
    return anytype_automation.test()
