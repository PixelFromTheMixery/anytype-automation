"""Scheduler for Anytype Automation"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from services.anytype.journal_service import JournalService
from services.anytype.task_service import TaskService

from utils.logger import logger

from settings import generate_settings

scheduler = AsyncIOScheduler()
settings = generate_settings()


def lifespan(_app: FastAPI) -> None:
    """Job Scheduler"""
    journal_service = (
        JournalService(settings) if settings.config.journal_space_id != "" else None
    )
    task_service = TaskService(settings, journal_service)

    logger.info("Adding jobs")
    if settings.config.local:
        logger.info("Local mode, no jobs to add")
    else:

        # Anytype
        logger.info("Adding daily rollover")
        scheduler.add_job(task_service.daily_rollover, "cron", hour=1)

        if settings.config.task_reset:
            logger.info("Adding task reset")
            scheduler.add_job(
                task_service.recurrent_check, "cron", hour="2-23", minute="*/30"
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
