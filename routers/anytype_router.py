"""Module that handles endpoints for anytype automation."""

from fastapi import APIRouter

from services.anytype_service import AnytypeAutomation
from utils.logger import logger

router = APIRouter()
anytype_automation = AnytypeAutomation()


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


@router.get("/test_anytype")
async def test_endpoint():
    """Endpoint for throwaway tests"""
    logger.info("Anytype test endpoint called")
    return anytype_automation.test()
