"""Module that handles endpoints for anytype automation."""

from fastapi import APIRouter

from models.data_request import DataRequest
from models.scan_request import ScanSpacesRequest
from models.search_request import SearchRequest
from services.anytype_service import AnytypeService
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


@router.post("/search", tags=["tools"])
async def search(search_request: SearchRequest):
    """Endpoint for searching objects"""
    logger.info("Search endpoint called")
    return anytype_automation.search(SearchRequest.model_dump(search_request))


@router.post("/scan_spaces", tags=["tools"])
async def scan_spaces(scan_request: ScanSpacesRequest):
    """Endpoint for scanning spaces for altering configuration file"""
    logger.info("Space scanner endpoint called")
    return anytype_automation.scan_spaces(ScanSpacesRequest.model_dump(scan_request))


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
