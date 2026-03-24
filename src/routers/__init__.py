"""Route manager for the api"""

from fastapi import APIRouter

from routers import anytype_router, general_router, pushover_router, toggl_router

router = APIRouter()

router.include_router(anytype_router.router, prefix="/anytype", tags=["anytype"])
router.include_router(pushover_router.router, prefix="/pushover", tags=["pushover"])
router.include_router(toggl_router.router, prefix="/toggl", tags=["toggl"])
router.include_router(general_router.router, prefix="/general", tags=["general"])
