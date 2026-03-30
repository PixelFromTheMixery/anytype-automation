"""API module to for sharing"""

import random
import time
from typing import Optional
import urllib

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import requests
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import logger

RETRIES: int = 3
DELAY: int = 2
TIMEOUT: int = 3


class EnvSettings(BaseSettings):
    """Env variables, usually tokens and env settings"""

    anytype_key: str
    allowed_ips: str
    allowed_urls: Optional[str] = None
    anytype_port: str = "31012"
    pushover_key: Optional[str] = None
    pushover_user: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("allowed_ips", "allowed_urls", mode="after")
    @classmethod
    def parse_comma_delimited(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


keys = EnvSettings()

RESPONSE_MAP = {
    "delete": lambda u, h: requests.delete(u, headers=h, timeout=TIMEOUT),
    "get": lambda u, h: requests.get(u, headers=h, timeout=TIMEOUT),
    "patch": lambda u, h, d: requests.patch(
        u,
        headers=h,
        timeout=TIMEOUT,
        json=d if isinstance(d, dict) else None,
        data=d if isinstance(d, str) else None,
    ),
    "post": lambda u, h, d: requests.post(
        u,
        headers=h,
        timeout=TIMEOUT,
        json=d if isinstance(d, dict) else None,
        data=d if isinstance(d, str) else None,
    ),
    "put": lambda u, h, d: requests.put(
        u,
        headers=h,
        timeout=TIMEOUT,
        json=d if isinstance(d, dict) else None,
        data=d if isinstance(d, str) else None,
    ),
}


def request_builder(url: str, data: dict = None, target: str = "anytype"):
    """Builds request scaffolding for API calls"""
    headers = {}
    data_pack = data if data else None

    if target == "anytype":
        headers = {
            "Authorization": "Bearer " + keys.anytype_key,
            "Content-Type": "application/json",
            "Anytype-Version": "2025-11-08",
        }

        url = "http://localhost:" + keys.anytype_port + url
    else:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data["token"] = keys.pushover_key
        data["user"] = keys.pushover_user

        data_pack = urllib.parse.urlencode(data)

    return url, headers, data_pack


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
    target: str = "anytype",
):
    """Makes web request with retry and some error handling"""

    url, headers, data_pack = request_builder(url, data, target)

    attempt = 0
    while True:
        try:
            logger.info(f"Attempt to {info}: {attempt} of {RETRIES}")

            response = (
                RESPONSE_MAP[category](url, headers, data_pack)
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


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """Class for IP allowlist middleware"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if request.client is not None:
            if request.client.host not in keys.allowed_ips:
                logger.error(
                    "Unauthorized access attempt from IP: " + request.client.host,
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Access denied: IP not allowed"},
                )
            return await call_next(request)
