"""API module to for sharing"""

import json
import os
import random
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
        logger.info(data)

    else:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = urllib.parse.urlencode(data)
    return headers, data


def exception_handler(e, result, attempt):
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

    headers, json_data = request_builder(url, data)

    attempt = 0
    while True:
        try:
            logger.info(f"Attempt to {info}: {attempt} of {RETRIES}")

            response = (
                RESPONSE_MAP[category](url, headers, json_data)
                if category in ["patch", "post", "put"]
                else RESPONSE_MAP[category](url, headers)
            )

            response.raise_for_status()
            return response.json()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            wait_time = 60 + random.uniform(0, 5)
            logger.warning(
                f"Network issue ({e}). Retrying infinitely... Next try in {wait_time:.1f}s"
            )
            time.sleep(wait_time)
            continue  # Restarts the 'while True' loop immediately

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                attempt += 1
                if attempt <= RETRIES:
                    logger.warning(
                        f"429 limit hit. Retry {attempt}/{RETRIES} in {DELAY}s..."
                    )
                    time.sleep(DELAY)
                    continue

            # If it's not a 429, or we ran out of 429 retries, handle normally
            attempt = exception_handler(e, response.json(), attempt)
            if attempt > RETRIES:
                raise

        except requests.exceptions.RequestException as e:
            # Catch-all for other request issues (DNS, etc.)
            attempt += 1
            if attempt > RETRIES:
                raise
            time.sleep(DELAY)
