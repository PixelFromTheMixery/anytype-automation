"""Module that handles endpoints for pushover automation."""

from fastapi import APIRouter

from services.anytype_service import AnytypeAutomation
from services.pushover_service import Pushover
from utils.logger import logger

router = APIRouter()
anytype_automation = AnytypeAutomation()
pushover = Pushover()


@router.get("/test_pushover")
async def create_repeating_obj():
    """Endpoint to update overdue or no collection tasks"""
    logger.info("Create repeating object endpoint called")
    return pushover.create_object_and_notify("ritual", "morning", " - Morning")

@router.get("/regular_task_alert")
async def task_status_reset():
    """Endpoint to update overdue or no collection tasks"""
    logger.info("Regular task alert endpoint called")
    return pushover.task_notify()
