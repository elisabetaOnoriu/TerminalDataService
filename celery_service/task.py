import json
import boto3
from celery_service.config import celery
import redis
from app.config.settings import get_settings

settings = get_settings()

sqs = boto3.client("sqs",
    region_name=str(settings.AWS_REGION),
    endpoint_url=str(settings.SQS_ENDPOINT_URL),
    aws_access_key_id=str(settings.AWS_ACCESS_KEY_ID),         
    aws_secret_access_key=str(settings.AWS_ACCESS_KEY_ID), )

SQS_QUEUE_URL = str(settings.SQS_QUEUE_URL)

r = redis.Redis(host="localhost", port=6379, db=2)
COUNTER_KEY = "sqs_emit_counter"
r.set("sqs_emit_counter", 0)

@celery.task(name="emit") #vezi cum se manifesta 
def emit():
    n=r.incr(COUNTER_KEY)
    msg = f"am emis mesajul: {n}"
    sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(msg))
    print(msg)
