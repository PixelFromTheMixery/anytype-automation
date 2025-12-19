"""Module that handles endpoints for anytype automation."""

from fastapi import APIRouter

from services.anytype_service import AnytypeAutomation
from utils.logger import logger

router = APIRouter()
anytype_automation = AnytypeAutomation()


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
async def search(search_criteria):
    """Endpoint for searching objects"""
    logger.info("Search endpoint called")
    return anytype_automation.search(search_criteria, False)


@router.post("/list_views")
async def list_views(
    view_id: str = "bafyreibhhlelfjv2kmtomcbgsprj3xjjx4xtw3oqh4qtvwfyquyg4gcbbi",
):
    """Endpoint to fetch automation list view"""
    logger.info("View fetcher endpoint called")
    return anytype_automation.view_list(view_id)


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
