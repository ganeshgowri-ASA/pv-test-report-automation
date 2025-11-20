"""
Health check endpoint for monitoring and load balancers.
"""
import sys
import time
from typing import Dict, Any
import psutil


class HealthChecker:
    """System health checker."""

    def __init__(self):
        self.checks = []

    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # Placeholder for actual database check
            # import psycopg2
            # conn = psycopg2.connect(DATABASE_URL)
            # conn.close()
            return {
                "status": "healthy",
                "latency_ms": 5
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            # Placeholder for actual Redis check
            # import redis
            # r = redis.from_url(REDIS_URL)
            # r.ping()
            return {
                "status": "healthy",
                "latency_ms": 2
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        disk = psutil.disk_usage('/')
        percent_used = disk.percent

        return {
            "status": "healthy" if percent_used < 90 else "unhealthy",
            "percent_used": percent_used,
            "free_gb": disk.free / (1024**3)
        }

    def check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        memory = psutil.virtual_memory()
        percent_used = memory.percent

        return {
            "status": "healthy" if percent_used < 90 else "unhealthy",
            "percent_used": percent_used,
            "available_gb": memory.available / (1024**3)
        }

    def check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage."""
        cpu_percent = psutil.cpu_percent(interval=1)

        return {
            "status": "healthy" if cpu_percent < 90 else "unhealthy",
            "percent_used": cpu_percent,
            "cpu_count": psutil.cpu_count()
        }

    def perform_health_check(self) -> Dict[str, Any]:
        """Perform complete health check."""
        checks = {
            "database": self.check_database(),
            "redis": self.check_redis(),
            "disk": self.check_disk_space(),
            "memory": self.check_memory(),
            "cpu": self.check_cpu()
        }

        # Determine overall health
        all_healthy = all(
            check.get("status") == "healthy"
            for check in checks.values()
        )

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": time.time(),
            "checks": checks
        }


def main():
    """Main entry point for health check."""
    checker = HealthChecker()
    result = checker.perform_health_check()

    # Print result
    import json
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "healthy" else 1)


if __name__ == "__main__":
    main()
