from utils.api_tools import make_call_with_retry
from utils.logger import logger

import os
from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi.responses import JSONResponse

load_dotenv()

router = APIRouter()


@router.get("/space")
async def test_endpoint():
    """Temp endpoint for testing"""
    logger.info("Test endpoint called")
    return make_call_with_retry("post", f"{os.getenv("URL")}spaces/{os.getenv("MAIN_SPACE_ID")}/search?limit=3", "getting main space", {"type":["Task"]})#, {"types":["task"]})