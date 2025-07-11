
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    #scheduler.add_job(notion_service.task_status_reset, 'cron', minute="*/5")
    #scheduler.add_job(notion_service.task_date_update, 'cron', day="*/1")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)