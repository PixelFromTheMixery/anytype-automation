"""Scheduler for Anytype Automation"""

from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from services.anytype.core_service import AnytypeService
from services.anytype.journal_service import JournalService
from services.anytype.task_service import TaskService
from services.pushover_service import PushoverService

anytype_core = AnytypeService()
anytype_journal = JournalService()
anytype_tasks = TaskService()
pushover = PushoverService()

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Job Scheduler"""
    # Anytype
    scheduler.add_job(anytype_tasks.recurrent_check, "cron", hour="7-21", minute="*/30")
    scheduler.add_job(anytype_core.daily_rollover, "cron", hour="23")
    ## Journal
    scheduler.add_job(anytype_journal.find_or_create_day_journal, "cron", hour="6")
    scheduler.add_job(anytype_journal.find_or_create_day_journal, "cron", hour="10")
    scheduler.add_job(anytype_journal.find_or_create_day_journal, "cron", hour="16")
    scheduler.add_job(anytype_journal.find_or_create_day_journal, "cron", hour="20")
    scheduler.add_job(anytype_journal.find_or_create_day_journal, "cron", hour="21")

    # Pushover
    ## Day Segment
    # scheduler.add_job(pushover.task_notify, "cron", hour="6")
    # scheduler.add_job(pushover.task_notify, "cron", hour="10")
    # scheduler.add_job(pushover.task_notify, "cron", hour="14")
    # scheduler.add_job(pushover.task_notify, "cron", hour="18")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
