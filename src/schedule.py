"""Scheduler for Anytype Automation"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from services.anytype.core_service import AnytypeService
from services.anytype.journal_service import JournalService
from services.anytype.task_service import TaskService
from services.anytype.space_service import SpaceService

from utils.logger import logger

from settings import generate_settings

scheduler = AsyncIOScheduler()
settings = generate_settings()


def lifespan(_app: FastAPI) -> None:
    """Job Scheduler"""
    anytype_space = SpaceService(settings)
    task_service = TaskService(settings)
    anytype_service = AnytypeService(settings, task_service, anytype_space)
    journal_service = JournalService(settings)

    logger.info("Adding jobs")
    if settings.config.local:
        logger.info("Local mode, no jobs to add")
    else:
        logger.info("Adding daily rollover")
        scheduler.add_job(anytype_service.daily_rollover, "cron", hour=23)

        # Anytype
        if settings.config.task_reset:
            logger.info("Adding task reset")
            scheduler.add_job(
                task_service.recurrent_check, "cron", hour="7-21", minute="*/30"
            )

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
