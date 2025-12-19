"""API module to for sharing"""

import json
import os
import time
import requests
from dotenv import load_dotenv

from utils.logger import logger

load_dotenv()


def make_call(
    category: str,
    url: str,
    info: str,
    data: dict | str | None = None,
    retries: int = 3,
    delay: int = 2,
    timeout: int = 3,
):
    """Makes web request with retry and some error handling"""
    headers = {}

    if "localhost" in url:
        data = json.dumps(data)
        headers = {
            "Authorization": f'Bearer {os.getenv("ANYTYPE_KEY")}',
            "Content-Type": "application/json",
            "Anytype-Version": "2025-05-20",
        }

    for attempt in range(1, retries + 1):
        result = None
        try:
            logger.info(f"Attempt to {info}. {attempt} of {retries}")
            if category == "delete":
                response = requests.delete(url, headers=headers, timeout=timeout)
            elif category == "get":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif category == "patch":
                response = requests.patch(
                    url, headers=headers, timeout=timeout, data=data
                )
            elif category == "post":
                response = requests.post(
                    url, headers=headers, timeout=timeout, data=data
                )
            elif category == "put":
                response = requests.put(
                    url, headers=headers, timeout=timeout, data=data
                )
            else:
                raise ValueError(f"Unknown category: {category}")

            result = response.json()
            response.raise_for_status()

            return result

        except requests.exceptions.RequestException as e:
            if result and result.get("status") == 429:
                if attempt < retries:
                    time.sleep(delay)
            elif result and "object deleted" in result.get("message"):
                return url.split("/")[-1]
            else:
                print(f"RequestException on attempt {attempt}: {e}")
                message = result.get("message") if result else None
                if message:
                    print(f"json response: {message}")
                break
