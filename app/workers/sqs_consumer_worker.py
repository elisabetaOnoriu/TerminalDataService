from concurrent.futures import ThreadPoolExecutor
import json
import time
from typing import Callable, Optional
import boto3
from app.workers.base_worker import BaseWorker

from app.config.settings import get_settings

settings = get_settings()
class SqsConsumerWorker(BaseWorker):
    def __init__(self, handler: Optional[Callable[[dict], None]] = None):
        super().__init__(name="SQSConsumer")
        self.queue_url =str(settings.SQS_QUEUE_URL)
        self.handler = handler
        self.thread_pool_size = settings.SQS_THREAD_POOL_SIZE
        self.wait_time = settings.SQS_WAIT_TIME_SECONDS
        self.max_messages = settings.SQS_MAX_MESSAGES
        self.sqs_endpoint = str(settings.SQS_ENDPOINT_URL) if settings.SQS_ENDPOINT_URL else None
        self.sqs = None
        self.executor = None

    def setup(self):
        if boto3 is None:
            raise RuntimeError("boto3 is not installed")
        
        self.sqs = boto3.client(
            "sqs",
            region_name=settings.AWS_REGION,
            endpoint_url=self.sqs_endpoint, # localhost, nu localstack 
            )
        
        self.executor= ThreadPoolExecutor(
            max_workers=self.thread_pool_size,
            thread_name_prefix="sqs-worker",
        )
        print(f"[{self.name}] connected to {self.queue_url} ({settings.AWS_REGION})")

    def process(self):
        try:
            resp = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                WaitTimeSeconds=self.wait_time,      
                MaxNumberOfMessages=self.max_messages 
            )
            
        except Exception as e:
            print("[SQS] receive_message failed: %s", e)
            return

        messages = resp.get("Messages", [])
        for m in messages:
            # time.sleep(4)
            self.executor.submit(self.handle_message, m)

    def handle_message(self, message: dict):
        receipt = message.get("ReceiptHandle")
        body = message.get("Body", "")

        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {"raw": body}

        self.handler(payload)
        time.sleep(3)

        if receipt:
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt)