from core.celery_app import celery_app

@celery_app.task(name="tasks.process_manual_workout_task")
def process_manual_workout_task(raw_doc_id: str, user_id: str):
    pass
