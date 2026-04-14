"""Scheduler for Anytype Automation"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from services.anytype.core_service import AnytypeService
from services.anytype.journal_service import JournalService
from services.anytype.space_service import SpaceService

from utils.logger import logger

from settings import generate_settings

scheduler = AsyncIOScheduler()
settings = generate_settings()


def lifespan(_app: FastAPI) -> None:
    """Job Scheduler"""
    journal_service = None
    if settings.config.journal_space_id != "":
        journal_service = JournalService(settings)
    anytype_space = SpaceService(settings)
    anytype_service = AnytypeService(settings, anytype_space)

    logger.info("Adding jobs")
    if settings.config.local:
        logger.info("Local mode, no jobs to add")
    else:
        logger.info("Adding daily rollover")
        scheduler.add_job(anytype_service.daily_rollover, "cron", hour=1)

        # Pushover
        ## Journal
        if settings.config.pushover:
            for hour in settings.config.pushover_journal_hours:
                logger.info("Adding journal reminders")

                scheduler.add_job(
                    journal_service.find_or_create_day_journal, "cron", hour=hour
                )
    scheduler.start()
    yield
    if not settings.config.local:
        scheduler.shutdown()
