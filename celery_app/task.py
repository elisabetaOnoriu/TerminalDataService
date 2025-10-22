import json
import logging
import os
import time
import boto3
from celery import Celery
import redis
from app.config.settings import get_settings
from logging_config import setup_logging

settings = get_settings()

setup_logging()
logger=logging.getLogger(__name__)

celery = Celery(main="sqs_producer_task", broker="redis://localhost:6379/0" , backend="redis://localhost:6379/1")
celery.conf.update(
    task_track_started=True,         
    result_expires=3600,             
    result_extended=True,            
)

sqs = boto3.client("sqs",
    region_name="us-east-1",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",         
    aws_secret_access_key="test", )

SQS_QUEUE_URL = "http://localhost:4566/000000000000/terminal-messages" 
r = redis.Redis(host="localhost", port=6379, db=2)
COUNTER_KEY = "sqs_emit_counter"

@celery.task(name="emit") #vezi cum se manifesta 
def emit():
    n=r.incr(COUNTER_KEY)
    msg = f"am emis mesajul: {n}"
    sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(msg))
    print(msg)

# @celery.task(name="bulk_emit")
# def bulk_emit(n: int = 10):
#     for i in range(n):
#         emit.delay(f"am emis mesajul: {i}") 

celery.conf.beat_schedule = {
    "beat-every-2s": {
        "task": "emit",
        "schedule": 2,
        }
}