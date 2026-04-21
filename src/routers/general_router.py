from http import HTTPStatus

from fastapi import APIRouter

from utils.logger import logger

from settings import generate_settings
from schedule import scheduler

router = APIRouter()


@router.get("/health", status_code=HTTPStatus.ACCEPTED)
async def get_health_endpoint():
    """Health Endpoint, should always return 200 OK"""
    return {"status": "ok"}


@router.get("/data")
async def get_ref_data():
    """Data Endpoint, should always return settings data"""
    logger.info("Data endpoint called")
    return generate_settings()


@router.get("/jobs", tags=["scheduled"])
async def get_jobs():
    """Jobs Endpoint, should always return scheduled tasks"""
    logger.info("Jobs endpoint called")
    jobs = scheduler.get_jobs()
    job_data = {}

    for job in jobs:
        job_data[job.id] = {
            "name": job.name,
            "func_ref": job.func_ref,
            "trigger": str(job.trigger),
            "next_run_time": (
                job.next_run_time.isoformat() if job.next_run_time else None
            ),
        }

    return job_data
