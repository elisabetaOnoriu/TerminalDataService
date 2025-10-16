import json, time, queue, boto3
from typing import Optional
from app.workers.base_worker import BaseWorker
from app.config.settings import get_settings

settings = get_settings()

class SqsProducerWorker(BaseWorker):
    def __init__(self, source_queue: Optional[queue.Queue] = None):
        super().__init__(name="SQSProducer")
        self.queue_url=str(settings.SQS_QUEUE_URL)
        self.region=settings.AWS_REGION
        self.endpoint_url=str(settings.SQS_ENDPOINT_URL) 
        self.source = source_queue or queue.Queue()
        self.sqs = None

    def setup(self):
        self.sqs = boto3.client("sqs", region_name=self.region, endpoint_url=self.endpoint_url)

    def enqueue(self, payload: dict):
        self.source.put(payload, timeout=1)


    def process(self): # a procesa, aici emit
        try:
            payload = self.source.get(timeout=1)
        except queue.Empty:
            time.sleep(0.2); return
        self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps(payload))
        print(f"[{self.name}] Sent message to {self.queue_url}: {payload}")
