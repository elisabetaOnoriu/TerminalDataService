import json
from app.celery_service.config import celery
from app.config.settings import get_settings
from app.celery_service.clients import get_redis, get_sqs

settings = get_settings()
COUNTER_KEY = "sqs_emit_counter"
@celery.task(name="emit") #to watch in docker 
def emit():
    sqs = get_sqs()
    r=get_redis()
    r.setnx("sqs_emit_counter", 0)
    n=r.incr(COUNTER_KEY)
    msg = f" message: {n}"
    sqs.send_message(QueueUrl= str(settings.SQS_QUEUE_URL), MessageBody=json.dumps(msg))
    print(f"emit {msg}")

@celery.task(name="consume")
def consume(msg: dict, receipt_handle: str):
    """Process a single SQS message."""
    sqs = get_sqs()
    print(f"consume {msg}")

    sqs.delete_message(QueueUrl= str(settings.SQS_QUEUE_URL), ReceiptHandle=receipt_handle)

@celery.task(name="poll_sqs")
def poll_sqs():
    """Poll SQS for messages and enqueue them for processing."""
    sqs = get_sqs()
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