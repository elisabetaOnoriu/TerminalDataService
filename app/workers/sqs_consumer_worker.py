import json
import time
from typing import Callable, Optional
import boto3
from app.workers.base_worker import BaseWorker


class SqsConsumerWorker(BaseWorker):
    def __init__(
        self,
        queue_url: str,
        region: str,
        handler: Callable[[dict], None],
        wait_time_s: int = 10,
        max_messages: int = 10,
        endpoint_url: Optional[str] = None,
        visibility_timeout_s: Optional[int] = None,
    ):
        super().__init__(name="SQSConsumer")
        self.queue_url = queue_url
        self.region = region
        self.handler = handler
        self.wait_time_s = wait_time_s
        self.max_messages = max_messages
        self.endpoint_url = endpoint_url
        self.visibility_timeout_s = visibility_timeout_s
        self.sqs = None

    def setup(self):
        if boto3 is None:
            raise RuntimeError("boto3 is not installed")
        self.sqs = boto3.client("sqs", region_name=self.region, endpoint_url=self.endpoint_url)
        print(f"[{self.name}] connected to {self.queue_url} ({self.region})")

    def process(self):
        params = {
            "QueueUrl": self.queue_url,
            "WaitTimeSeconds": self.wait_time_s,
            "MaxNumberOfMessages": self.max_messages,
        }
        if self.visibility_timeout_s is not None:
            params["VisibilityTimeout"] = self.visibility_timeout_s

        resp = self.sqs.receive_message(**params)
        messages = resp.get("Messages", [])
        if not messages:
            time.sleep(0.2)
            return

        for m in messages:
            receipt = m["ReceiptHandle"]
            body_raw = m.get("Body", "")
            try:
                try:
                    payload = json.loads(body_raw)
                except json.JSONDecodeError:
                    payload = {"raw": body_raw}
                self.handler(payload)
                self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt)
            except Exception as e:
                print(f"[{self.name}] handler failed: {e}")
