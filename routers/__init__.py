from routers import anytype_router, general_router

from fastapi import APIRouter

router = APIRouter()

router.include_router(anytype_router.router, tags=["anytype (basic)"])
router.include_router(general_router.router, tags=["general"])
