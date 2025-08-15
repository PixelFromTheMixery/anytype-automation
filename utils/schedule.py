"""Scheduler for Anytype Automation"""

from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from services.anytype_service import AnytypeAutomation
from services.pushover_service import Pushover

anytype_automation = AnytypeAutomation()
pushover = Pushover()

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Job Scheduler"""
    # Anytype
    scheduler.add_job(
        anytype_automation.recurrent_check, "cron", hour="7-21", minute="*/30"
    )
    scheduler.add_job(anytype_automation.daily_rollover, "cron", hour="23")

    # Pushover
    ## Day Segment
    scheduler.add_job(pushover.task_notify, "cron", hour="6")
    scheduler.add_job(pushover.task_notify, "cron", hour="10")
    scheduler.add_job(pushover.task_notify, "cron", hour="14")
    scheduler.add_job(pushover.task_notify, "cron", hour="18")
    ## Rituals
    # scheduler.add_job(
    #     pushover.create_object_and_notify,
    #     "cron",
    #     args=("ritual", "morning", " - Morning"),
    #     hour="5",
    #     minute="55",
    # )
    # scheduler.add_job(
    #     pushover.create_object_and_notify,
    #     "cron",
    #     args=("ritual", "evening", " - Evening"),
    #     hour="20",
    # )
    # scheduler.add_job(
    #     pushover.create_object_and_notify,
    #     "cron",
    #     args=("planning_log", "planning"),
    #     hour="21",
    # )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
