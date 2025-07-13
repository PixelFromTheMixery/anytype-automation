from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.exception import AnytypeException
from utils.logger import logger


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except AnytypeException as exc:
            logger.error(exc)
            return JSONResponse(
                status_code = exc.status,
                content = {"Notion error": exc.message}
            )
        except Exception as exc:
            logger.error(exc)
            print(exc)
            raise HTTPException(
                status_code = 500,
                detail= {"Misc error": str(exc)}
            )
