"""Main entry point for AnyTYpe Automation API"""

from http import HTTPStatus
from fastapi import FastAPI

from utils.docs import description, tags_metadata
from utils.logger import logger
from middlewares.exception_middleware import ExceptionMiddleware
import routers


app = FastAPI(
    title="AnyType Automation",
    description=description,
    summary="API endpoints for the Anytype App",
    openapi_tags=tags_metadata,
)

app.add_middleware(ExceptionMiddleware)

@app.get("/", tags=["general"], status_code=HTTPStatus.ACCEPTED)
async def get_root():
    """Root Endpoint"""
    logger.info("Root endpoint called")
    return {"Intervalia": "Currently maintained by Pixel from the Mixery"}

app.include_router(routers.router)
