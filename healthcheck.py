#!/usr/bin/env python3
"""
Health Check Script for PV Test Automation System
Verifies all services are operational
"""

import requests
import sys
import time
from typing import Dict, Tuple


def check_service(name: str, url: str, timeout: int = 5) -> Tuple[bool, str]:
    """Check if a service is healthy"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, "OK"
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def main():
    """Main health check routine"""
    services = {
        'Streamlit App': 'http://localhost:8501/_stcore/health',
        'API Server': 'http://localhost:8000/health',
        'Nginx': 'http://localhost/health',
        'MinIO': 'http://localhost:9000/minio/health/live',
        'RabbitMQ': 'http://localhost:15672/api/health/checks/alarms',
    }

    print("=" * 60)
    print("PV Test Automation System - Health Check")
    print("=" * 60)
    print()

    all_healthy = True
    results: Dict[str, Tuple[bool, str]] = {}

    for service_name, service_url in services.items():
        is_healthy, message = check_service(service_name, service_url)
        results[service_name] = (is_healthy, message)

        status_icon = "✓" if is_healthy else "✗"
        status_color = "\033[92m" if is_healthy else "\033[91m"  # Green or Red
        reset_color = "\033[0m"

        print(f"{status_icon} {status_color}{service_name:20s}{reset_color}: {message}")

        if not is_healthy:
            all_healthy = False

    print()
    print("=" * 60)

    if all_healthy:
        print("\033[92m✓ All services are healthy\033[0m")
        print("=" * 60)
        return 0
    else:
        print("\033[91m✗ Some services are unhealthy\033[0m")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
