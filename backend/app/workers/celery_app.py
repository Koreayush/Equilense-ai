"""
app/workers/celery_app.py
=========================
Central Celery application bootstrap.
"""

from celery import Celery
from kombu import Queue   
from app.core.config import settings


# ─────────────────────────────────────────────────────────────
# Create Celery App
# ─────────────────────────────────────────────────────────────

celery = Celery(
    "unbiased_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)


# ─────────────────────────────────────────────────────────────
# Core Configuration
# ─────────────────────────────────────────────────────────────

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    task_track_started=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24 hours

    #  QUEUE SYSTEM (SCALING)
    task_queues=(
        Queue("default"),
        Queue("model_audit"),
        Queue("full_pipeline"),
    ),

    #  ROUTING TASKS TO QUEUES
    task_routes={
        "app.workers.model_audit_worker.run_model_audit_task": {
            "queue": "model_audit"
        },
        "app.workers.model_audit_worker.run_full_model_pipeline_task": {
            "queue": "full_pipeline"
        },
    },
)


# ─────────────────────────────────────────────────────────────
#  Auto-discover tasks
# ─────────────────────────────────────────────────────────────

celery.autodiscover_tasks(["app.workers"])