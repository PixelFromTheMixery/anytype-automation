from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.config import Config
from utils.exception import AnytypeException
from utils.logger import logger
from utils.pushover import PushoverUtils


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions globally."""

    def __init__(self, app):
        super().__init__(app)
        self.pushover = PushoverUtils()
        self.send = Config.get()["settings"]["pushover"]

    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except AnytypeException as exc:
            logger.error(exc)
            return JSONResponse({"Anytype error": exc.message}, exc.status)
        except Exception as exc:
            logger.error(
                f"Unhandled exception processing {request.method}, {request.url.path}. Issue: {exc}"
            )

            error_type = type(exc).__name__
            content = (
                f"Error type: {error_type}, "
                f"Occured at: {request.method} {request.url.path}, "
                f"suggested fix: {exc.args},"
            )
            if self.send:
                self.pushover.send_message(error_type, content, priority=1)
            return JSONResponse(content, 500)
