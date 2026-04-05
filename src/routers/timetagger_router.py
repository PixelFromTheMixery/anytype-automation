"""Module that handles endpoints for pushover automation."""

from functools import lru_cache

from fastapi import APIRouter

from services.timetagger_service import TimetaggerService

from utils.logger import logger

from settings import generate_settings


@lru_cache
def get_timetagger_service():
    return TimetaggerService(generate_settings())


router = APIRouter()

timetagger = get_timetagger_service()


@router.get("/toggle_timer/{object_id}")
async def toggle_time(object_id: str):
    """End point for starting a timer"""
    logger.info("Timer toggle Endpoint called")
    return timetagger.toggle(object_id)
