"""Main entry point for AnyTYpe Automation API"""

from http import HTTPStatus

from fastapi import FastAPI


from middlewares.exception_middleware import ExceptionMiddleware
from utils.api_tools import IPAllowlistMiddleware
from utils.docs import DESCRIPTION, TAGS
from utils.logger import logger

import routers
from schedule import lifespan

from settings import generate_settings


def get_settings():
    """Generates Settings singleton"""
    return generate_settings()


settings = get_settings()


def create_app() -> FastAPI:
    """Configures the server"""
    fastapi_app = FastAPI(
        title="AnyType Automation",
        description=DESCRIPTION,
        summary="API endpoints for the Anytype App",
        root_path="/aa-api",
        openapi_tags=TAGS,
        lifespan=lifespan,
    )

    fastapi_app.add_middleware(ExceptionMiddleware)
    fastapi_app.add_middleware(IPAllowlistMiddleware)

    fastapi_app.include_router(routers.router)

    return fastapi_app


app = create_app()


@app.get("/", tags=["general"], status_code=HTTPStatus.ACCEPTED)
async def get_root():
    """Root Endpoint"""
    logger.info("Root endpoint called")
    return {"Anytype Automation": "Currently maintained by Pixel from the Mixery"}
