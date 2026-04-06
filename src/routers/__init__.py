from fastapi import APIRouter

from routers import anytype_router, general_router

from settings import generate_settings

settings = generate_settings()
router = APIRouter()


router.include_router(anytype_router.router, prefix="/anytype", tags=["anytype"])
router.include_router(general_router.router, prefix="/general", tags=["general"])


if settings.config.timetagger:
    from routers import timetagger_router

    router.include_router(
        timetagger_router.router, prefix="/timetagger", tags=["timetagger"]
    )
