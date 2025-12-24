from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.exception import AnytypeException
from utils.logger import logger
from utils.pushover import PushoverUtils
import traceback


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions globally."""

    def __init__(self, app):
        super().__init__(app)
        self.pushover = PushoverUtils()

    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except AnytypeException as exc:
            logger.error(exc)
            return JSONResponse(
                status_code=exc.status, content={"Anytype error": exc.message}
            )
        except Exception as exc:
            logger.exception(
                f"Unhandled exception processing {request.method}, {request.url.path}"
            )
            tb = traceback.format_exc()
            message = (
                f"500 Internal Server Error\n"
                f"Request: {request.method} {request.url.path}\n"
                f"Error: {exc}\n\n"
                f"Traceback:\n{tb}"
            )
            # self.pushover.send_message("500 Internal Server Error", message, priority=1)
            raise HTTPException(
                status_code=500, detail={"Misc error": "Internal Server Error"}
            ) from exc
