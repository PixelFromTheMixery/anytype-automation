from http import HTTPStatus
from fastapi import APIRouter, Depends


from services.health_service import HealthService
from utils.data import DataManager
from utils.logger import logger


router = APIRouter()


def get_health_service():
    return HealthService()


@router.get("/health", status_code=HTTPStatus.ACCEPTED)
async def get_health_endpoint(
    health_service: HealthService = Depends(get_health_service),
):
    """Health Endpoint, should always return 200 OK"""
    logger.info("Health endpoint called")
    return await health_service.check_health("OK")


@router.get("/reload", tags=["tools"])
async def reload():
    """Endpoint for Reloading local DATA"""
    logger.info("Reload DATA endpoint called")
    DataManager.reload()
    return DataManager.data
