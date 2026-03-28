from http import HTTPStatus

from fastapi import APIRouter

from utils.logger import logger


router = APIRouter()


@router.get("/health", status_code=HTTPStatus.ACCEPTED)
async def get_health_endpoint():
    """Health Endpoint, should always return 200 OK"""
    logger.info("Health endpoint called")
    return await {"status": "ok"}
