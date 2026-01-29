from models.health import HealthStatus


class HealthService:
    def check_health(self, status: str) -> HealthStatus:
        return HealthStatus(status=status)
