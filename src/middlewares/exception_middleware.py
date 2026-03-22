"""Exception Middleware for managing errors"""

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import requests

from utils.config import Config
from utils.exception import AnytypeException
from utils.logger import logger
from utils.pushover import PushoverUtils


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions globally."""

    def __init__(self, app):
        super().__init__(app)
        self.pushover = PushoverUtils()
        self.local = Config.data["local"]

    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except AnytypeException as exc:
            logger.error(exc)
            return JSONResponse({"Anytype error": exc.message}, exc.status)
        except Exception as exc:
            error_type = type(exc).__name__
            detail = str(exc)

            if isinstance(exc, requests.exceptions.HTTPError):
                try:
                    detail = exc.response.json().get("message", detail)
                except Exception:
                    detail = exc.response.text[:100]

            logger.error(f"Unhandled exception at {request.url.path}: {detail}")

            content = {
                "status": "error",
                "type": error_type,
                "message": detail,
                "path": f"{request.method} {request.url.path}",
            }

            if not self.local:
                self.pushover.send_message(
                    f"API Error: {error_type}", detail, priority=1
                )

            return JSONResponse(content, 500)
