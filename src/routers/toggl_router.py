from functools import lru_cache

from fastapi import APIRouter

from services.toggl_service import TogglService

from utils.logger import logger

from settings import generate_settings


@lru_cache
def get_toggl_service():
    return TogglService(generate_settings())


router = APIRouter()
toggl = get_toggl_service()


@router.get("/{project}/{task_name}/start_timer")
def start_timer(project, task_name):
    """End point for starting a timer with a based on task name and project"""
    logger.info("Endpoint for starting timer for: ")
    logger.info(f"{task_name} in {project}")
    toggl.start_timer(project, task_name)
