from core.celery_app import celery_app

@celery_app.task(name="tasks.ping_task")
def ping_task():
    return "pong"
