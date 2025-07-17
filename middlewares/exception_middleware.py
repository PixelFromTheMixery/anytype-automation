from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.exception import AnytypeException
from utils.logger import logger
from utils.pushover import Pushover

class ExceptionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions globally."""

    def __init__(self):
        self.pushover = Pushover()

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
            raise HTTPException(
                status_code=500, detail={"Misc error": str(exc)}
            ) from exc
        finally:
            self.pushover.send_message("An error occurred in Anytype Automation")
