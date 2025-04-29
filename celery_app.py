import os
from dotenv import load_dotenv
from celery import Celery

# Load your .env (must contain CELERY_BROKER_URL and CELERY_RESULT_BACKEND)
load_dotenv()

# Get Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")

# Construct Redis URLs
broker_url = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
backend_url = os.getenv("CELERY_RESULT_BACKEND", broker_url)

# This is the Celery "app" instance
celery_app = Celery(
    "reply_bot",
    broker=broker_url,
    backend=backend_url,
)

# Configure Celery
celery_app.conf.update(
    task_soft_time_limit=60,
    task_time_limit=120,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,  # Prevents worker from taking too many tasks
    task_acks_late=True,  # Tasks are acknowledged after execution
    task_reject_on_worker_lost=True,  # Requeue tasks if worker dies
)

# Windows-specific settings
if os.name == 'nt':  # Windows
    celery_app.conf.update(
        worker_pool='solo',  # Use solo pool instead of prefork
        worker_max_tasks_per_child=1,
        worker_concurrency=1,
        task_always_eager=False,
        task_eager_propagates=False,
    )

# Directly import tasks to ensure registration
import app.celery_tasks
