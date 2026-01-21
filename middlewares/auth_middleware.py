"""Middleware to restrict access based on IP address"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import logger
from utils.pushover import PushoverUtils


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """Class for IP allowlist middleware"""

    def __init__(self, app):
        super().__init__(app)
        self.pushover = PushoverUtils()
        self.allowed_ips = [
            "100.89.127.5",
            "100.118.137.32",
            "100.125.9.80",
            "192.168.50.41",
        ]

    async def dispatch(self, request: Request, call_next):
        if request.client is not None:
            client_ip = request.client.host
            if client_ip not in self.allowed_ips:
                self.pushover.send_message(
                    "UNAUTHORIZED ACCESS ATTEMPT",
                    2,
                )
                logger.error(
                    f"Unauthorized access attempt from IP: {client_ip}.",
                )
            return await call_next(request)
