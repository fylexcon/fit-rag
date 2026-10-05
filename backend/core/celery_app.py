from celery import Celery
from core.config import settings

celery_app = Celery(
    "fitness_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.test_tasks", "tasks.workout_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "heartbeat-every-10-minutes": {
        "task": "tasks.heartbeat",
        "schedule": crontab(minute="*/10"),
    }
}
