import json, time, queue, boto3
from typing import Optional
from app.workers.base_worker import BaseWorker

class SqsProducerWorker(BaseWorker):
    def __init__(self, queue_url: str, region: str, endpoint_url: Optional[str] = None, source_queue: Optional[queue.Queue] = None):
        super().__init__(name="SQSProducer")
        self.queue_url, self.region, self.endpoint_url = queue_url, region, endpoint_url
        self.source = source_queue or queue.Queue()
        self.sqs = None

    def setup(self):
        self.sqs = boto3.client("sqs", region_name=self.region, endpoint_url=self.endpoint_url)

    def enqueue(self, payload: dict):
        self.source.put(payload, timeout=1)

    def process(self):
        try:
            payload = self.source.get(timeout=1)
        except queue.Empty:
            time.sleep(0.2); return
        self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps(payload))
