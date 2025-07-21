"""Module that handles endpoints for anytype automation."""

from dotenv import load_dotenv
from fastapi import APIRouter


from services.anytype_automation import AnytypeAutomation
from utils.anytype import AnyTypeUtils
from utils.logger import logger

load_dotenv()

router = APIRouter()
anytype_automation = AnytypeAutomation()
anytype_utils = AnyTypeUtils()


@router.get("/daily_rollover")
async def task_status_reset():
    """Endpoint to update overdue or no collection tasks"""
    logger.info("Daily rollover endpoint called")
    return anytype_automation.daily_rollover()


@router.get("/automation_list_view")
async def automation_list_view():
    """Endpoint to fetch automation list view"""
    logger.info("View fetcher endpoint called")
    return anytype_automation.view_list()


@router.get("/recurrent_check")
async def recurrent_tcheck():
    """Endpoint for task maintenance"""
    logger.info("Recurrent check endpoint called")
    return anytype_automation.recurrent_check()


@router.get("/search")
async def search_endpoint(criteria: str, obj: bool = True, search_filer: str = ""):
    """Endpoint for searching a space"""
    logger.info("Search endpoint called")
    return anytype_utils.search_by_type_and_or_name(criteria, obj, search_filer)


@router.get("/test")
async def test_endpoint():
    """Endpoint for throwaway tests"""
    logger.info("Test endpoint called")
    return anytype_utils.test()
