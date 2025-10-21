import logging
import os
import time
from celery import Celery

from logging_config import setup_logging

setup_logging()
logger=logging.getLogger(__name__)

celery = Celery("tasks", broker="redis://localhost:6379/0" , backend="redis://localhost:6379/1")
celery.conf.update(
    task_track_started=True,         
    result_expires=3600,             
    result_extended=True,            
)

@celery.task(bind=True)
def process_event(self, msg: dict):
    time.sleep(10)
    logger.info("[pid=%s task_id=%s] Event received: %s",
    os.getpid(), self.request.id, msg)  
    return {"received": msg, "task_id": self.request.id}