"""Middleware to restrict access based on IP address"""
import os
import signal
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import logger
from utils.pushover import Pushover

class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """Class for IP allowlist middleware"""
    def __init__(self, app):
        super().__init__(app)
        self.pushover = Pushover()
        self.allowed_ips = [
        "10.147.17.16",
        "10.147.17.211",
        "10.147.17.63",
        "10.147.17.107",
    ]
    async def dispatch(self, request: Request, call_next):
        if request.client is not None:
            client_ip = request.client.host
            if client_ip not in self.allowed_ips:
                self.pushover.send_message(
                    "UNAUTHORIZED ACCESS ATTEMPT", 
                    f"Unauthorized access attempt from IP: {client_ip}. Shutting down.", 2
                )
                logger.error("Unauthorized access attempt from IP: %s. Shutting down.", client_ip)
                os.kill(os.getpid(), signal.SIGINT)
            return await call_next(request)
