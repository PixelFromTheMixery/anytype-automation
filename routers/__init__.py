"""Route manager for the api"""

from fastapi import APIRouter

from routers import anytype_router, general_router, pushover_router

router = APIRouter()

router.include_router(anytype_router.router, tags=["anytype"])
router.include_router(pushover_router.router, tags=["pushover"])
router.include_router(general_router.router, tags=["general"])
