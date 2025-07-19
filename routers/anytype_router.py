"""Module that handles endpoints for anytype automation."""

from dotenv import load_dotenv
from fastapi import APIRouter


from services.anytype_automation import AnytypeAutomation
from utils.anytype import AnyTypeUtils
from utils.api_tools import make_call
from utils.logger import logger

load_dotenv()

router = APIRouter()
anytype_automation = AnytypeAutomation()
anytype_utils = AnyTypeUtils()


@router.get("/daily_rollover")
async def task_status_reset():
    """Endpoint to update overdue or no collection tasks"""
    logger.info("Daily rollover endpoint called")
    return anytype_automation.daily_rollover()


@router.get("/automation_list_view")
async def automation_list_view():
    """Endpoint to fetch automation list view"""
    logger.info("View fetcher endpoint called")
    return anytype_automation.view_list()


@router.get("/recurrent_check")
async def recurrent_tcheck():
    """Endpoint for task maintenance"""
    logger.info("Recurrent check endpoint called")
    return anytype_automation.recurrent_check()


@router.get("/test")
async def test_endpoint():
    """Temp endpoint for testing"""
    # logger.info("Test endpoint called")
    # url = "http://localhost:31009/v1/spaces/"
    # url += "bafyreihydnqhxtkwiv55kqafoxyfk3puf7fm54n6txjo34iafbjujbbo2a.2bx9tjqqte21g/"
    # url += "properties/"
    # url += "bafyreicuswtnsqujbi2q7fmwvpszhnrkhvmb7puu6r3pg3pbflcqfve7ay/"
    # url += "tags"
    # return make_call("post", url, "getting automation list objects", payload)
    # return make_call("get", url, "getting automation list objects")
    return anytype_utils.get_views_list()