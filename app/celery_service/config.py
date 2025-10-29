from celery import Celery
from app.config.settings import get_settings
# from app.celery_service.clients import get_redis, get_sqs

# settings = get_settings()
# celery = Celery(main="sqs_task", broker="redis://localhost:6379/0" , backend="redis://localhost:6379/1")
celery = Celery(main="sqs_task", broker="redis://redis:6379/0" , backend="redis://redis:6379/1")

celery.conf.update(
    result_expires=3600,             
    result_extended=True,            
)

celery.conf.beat_schedule = {
       "poll-sqs-every-3s": {
        "task": "poll_sqs",
        "schedule": 3,                          
    },
    "beat-every-2s": {
        "task": "emit",
        "schedule": 2,
        }
}