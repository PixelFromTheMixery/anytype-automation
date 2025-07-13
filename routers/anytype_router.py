from services.antype_service import AnytypeService
from utils.anytype import AnyTypeUtils
from utils.api_tools import make_call_with_retry
from utils.logger import logger

import json
from dotenv import load_dotenv
from fastapi import APIRouter

load_dotenv()

router = APIRouter()
anytype_service = AnytypeService()
anytype_utils = AnyTypeUtils()


@router.get("/daily_rollover")
async def task_status_reset():
    """Endpoint to migrate or reset tasks"""
    logger.info("Daily rollover endpoint called")
    return anytype_service.daily_rollover()


@router.get("/automation_list_view")
async def automation_list_view():
    """Endpoint to fetch automation list view"""
    logger.info("View fetcher endpoint called")
    return anytype_service.view_list()


@router.get("/test")
async def test_endpoint():
    """Temp endpoint for testing"""
    logger.info("Test endpoint called")
    url = "http://localhost:31009/v1/spaces/"
    url += "bafyreihydnqhxtkwiv55kqafoxyfk3puf7fm54n6txjo34iafbjujbbo2a.2bx9tjqqte21g/"
    url += "lists/"
    url += "bafyreibhhlelfjv2kmtomcbgsprj3xjjx4xtw3oqh4qtvwfyquyg4gcbbi/"
    url += "views/"
    url += "6872e16da7ace015b4a15bdc/"
    url += "objects"
    return make_call_with_retry("get", url, "getting automation list objects")
