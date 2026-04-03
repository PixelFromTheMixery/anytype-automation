from fastapi import APIRouter

from routers import anytype_router, general_router, timetagger_router

from settings import generate_settings

settings = generate_settings()
router = APIRouter()


router.include_router(anytype_router.router, prefix="/anytype", tags=["anytype"])
router.include_router(general_router.router, prefix="/general", tags=["general"])

if settings.config.pushover:
    from routers import pushover_router

    router.include_router(pushover_router.router, prefix="/pushover", tags=["pushover"])

if settings.config.timetagger:
    pass