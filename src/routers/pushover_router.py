"""Module that handles endpoints for pushover automation."""

from functools import lru_cache

from fastapi import APIRouter

from services.anytype.journal_service import JournalService
from services.pushover_service import PushoverService
from utils.logger import logger

from settings import generate_settings


@lru_cache
def get_journal_service():
    return JournalService(generate_settings())


router = APIRouter()

settings = generate_settings()
anytype_journal = get_journal_service()
pushover = PushoverService()


@router.get("/day_journal", tags=["scheduled"])
async def day_journal():
    """Endpoint to fetch or create day journal instance id"""
    logger.info("Day Journal endpoint called")
    return anytype_journal.find_or_create_day_journal()


@router.get("/regular_task_alert")
async def task_status_reset():
    """Endpoint to update overdue or no collection tasks"""
    logger.info("Regular task alert endpoint called")
    return pushover.task_notify()


@router.get("/pushover_test")
async def pushover_test():
    """Endpoint for testing pushover notifications"""
    logger.info("Pushover test endpoint called")
    return pushover.pushover_test()
