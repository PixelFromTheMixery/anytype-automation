"""Scheduler for Anytype Automation"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.anytype_service import AnytypeService

anytype_service = AnytypeService()
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Job Scheduler"""
    scheduler.add_job(anytype_service.recurrent_check, "cron", minute="*/30")
    scheduler.add_job(anytype_service.daily_rollover, "cron", hour="*/23")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
