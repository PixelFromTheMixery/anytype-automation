from models.health import HealthStatus


class HealthService:
    async def check_health(self, status: str) -> HealthStatus:
        return HealthStatus(status=status)
