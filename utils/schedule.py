"""Scheduler for Anytype Automation"""

from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.anytype_automation import AnytypeAutomation

anytype_automation = AnytypeAutomation()
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan():
    """Job Scheduler"""
    scheduler.add_job(
        anytype_automation.recurrent_check, "cron", hour="7-21", minute="*/30"
    )
    scheduler.add_job(anytype_automation.daily_rollover, "cron", hour="*/23")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
