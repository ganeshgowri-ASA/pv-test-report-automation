"""
Celery Application Configuration
Background task processing for PV Test Automation
"""

from celery import Celery
import os

# Get broker URL from environment
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'amqp://admin:changeme@rabbitmq:5672')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create Celery app
celery_app = Celery(
    'pv_test_automation',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['api.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routes
celery_app.conf.task_routes = {
    'api.tasks.process_data_upload': {'queue': 'data_processing'},
    'api.tasks.generate_report': {'queue': 'report_generation'},
    'api.tasks.run_llm_analysis': {'queue': 'llm_processing'},
    'api.tasks.send_email_notification': {'queue': 'notifications'},
}

if __name__ == '__main__':
    celery_app.start()
