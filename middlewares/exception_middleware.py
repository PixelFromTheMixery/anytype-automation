from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.exception import AnytypeException
from utils.logger import logger
from utils.pushover import PushoverUtils

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
            logger.error(exc)
            print(exc)
            self.pushover.send_message("500", str(exc), priority=1)
            raise HTTPException(
                status_code=500, detail={"Misc error": str(exc)}
            ) from exc
