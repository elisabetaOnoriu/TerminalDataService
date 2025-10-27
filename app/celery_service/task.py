import json
import boto3
from app.celery_service.config import celery
import redis
from app.config.settings import get_settings
from app.celery_service.init import sqs, SQS_QUEUE_URL, r, COUNTER_KEY

settings = get_settings()

@celery.task(name="emit") #vezi cum se manifesta cand fol docker 
def emit():
    n=r.incr(COUNTER_KEY)
    msg = f" mesajul: {n}"
    sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(msg))
    print(f"am emis {msg}")

@celery.task(name="consume")
def consume(msg: dict, receipt_handle: str):
    """Process a single SQS message."""

    print(f"consum {msg}")

    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)

@celery.task(name="poll_sqs")
def poll_sqs():
    """Poll SQS for messages and enqueue them for processing."""
    resp = sqs.receive_message(
        QueueUrl=str(settings.SQS_QUEUE_URL),
        WaitTimeSeconds=int(settings.SQS_WAIT_TIME_SECONDS),      
        MaxNumberOfMessages=int(settings.SQS_MAX_MESSAGES),
        VisibilityTimeout=int(settings.SQS_VISIBILITY_TIMEOUT)  
    )

    msgs = resp.get("Messages", [])
    for m in msgs:
        body = json.loads(m["Body"])
        consume.apply_async(args=[body, m["ReceiptHandle"]])