"""API module to for sharing"""

import json
import os
import time
import urllib
import requests
from dotenv import load_dotenv

from utils.logger import logger

load_dotenv()

RETRIES: int = 3
DELAY: int = 2
TIMEOUT: int = 3

RESPONSE_MAP = {
    "delete": lambda u, h: requests.delete(u, headers=h, timeout=TIMEOUT),
    "get": lambda u, h: requests.get(u, headers=h, timeout=TIMEOUT),
    "patch": lambda u, h, d: requests.patch(u, headers=h, timeout=TIMEOUT, data=d),
    "post": lambda u, h, d: requests.post(u, headers=h, timeout=TIMEOUT, data=d),
    "put": lambda u, h, d: requests.put(u, headers=h, timeout=TIMEOUT, data=d),
}


def request_builder(url, data=None):
    """Builds request scaffolding for API calls"""
    headers = {}

    if "localhost" in url:
        headers = {
            "Authorization": f'Bearer {os.getenv("ANYTYPE_KEY")}',
            "Content-Type": "application/json",
            "Anytype-Version": "2025-11-08",
        }
        data = json.dumps(data) if data else None

    else:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = urllib.parse.urlencode(data)
    return headers, data


def exception_handler(e, result, attempt):
    if result and result.get("status") == 429:
        if attempt < RETRIES:
            time.sleep(DELAY)
            return attempt + 1
    else:
        print(f"RequestException on attempt {attempt}: {e}")
        message = result.get("message") if result else None
        if message:
            print(f"json response: {message}")
        return RETRIES + 1


def make_call(
    category: str,
    url: str,
    info: str,
    data: dict | str | None = None,
):
    """Makes web request with retry and some error handling"""

    headers, data = request_builder(url, data)

    for attempt in range(1, RETRIES + 1):
        result = None
        try:
            logger.info(f"Attempt to {info}. {attempt} of {RETRIES}")

            response = (
                RESPONSE_MAP[category](url, headers, data)
                if category in ["patch", "post", "put"]
                else RESPONSE_MAP[category](url, headers)
            )

            result = response.json()
            response.raise_for_status()

            return result

        except requests.exceptions.RequestException as e:
            attempt = exception_handler(e, result, attempt)
