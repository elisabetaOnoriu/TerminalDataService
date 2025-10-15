from concurrent.futures import ThreadPoolExecutor
import json
import time
from typing import Callable, Optional
import boto3
from app.config.settings import Settings
from app.workers.base_worker import BaseWorker

class SqsConsumerWorker(BaseWorker):
    def __init__(
        self,
        settings:Settings,
        queue_url: str,
        region: str,
        handler: Callable[[dict], None],
        wait_time_s: int = 10,
        max_messages: int = 10,
        endpoint_url: Optional[str] = None,
    ):
        super().__init__(name="SQSConsumer")
        self.queue_url = queue_url
        self.region = region
        self.handler = handler
        self.wait_time_s = wait_time_s
        self.max_messages = max_messages
        self.endpoint_url = endpoint_url
        self.sqs = None
        self.executor = None

    def setup(self):
        if boto3 is None:
            raise RuntimeError("boto3 is not installed")
        self.sqs = boto3.client("sqs", region_name=self.region, endpoint_url=self.endpoint_url)
        self.executor= ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="sqs-worker",
        )
        print(f"[{self.name}] connected to {self.queue_url} ({self.region})")

    def process(self):
        try:
            resp = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                WaitTimeSeconds=self.wait_time_s,      
                MaxNumberOfMessages=self.max_messages 
            )
            
        except Exception as e:
            print("[SQS] receive_message failed: %s", e)
            return

        messages = resp.get("Messages", [])
        for m in messages:
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