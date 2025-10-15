import json
import time
import queue
from typing import Optional
from kafka import KafkaProducer
from app.workers.base_worker import BaseWorker

class KafkaProducerWorker(BaseWorker):
    """
    Produces messages to a Kafka topic from a queue-like source.
    """

    def __init__(self, topic: str, server:str ,source_queue: Optional[queue.Queue] = None):
        """ Initialize the worker with Kafka connection details and a source queue """
        super().__init__(name=f"KafkaProducer-{topic}")
        self.topic = topic
        self.server = server
        self.source = source_queue or queue.Queue()
        self.p = None

    def setup(self):
        print(f"[{self.name}] Connecting to {self.server} topic '{self.topic}'...")
        self.p = KafkaProducer(
            bootstrap_servers=[self.server],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def process(self):
        try:
            payload = self.source.get(timeout=1)
        except queue.Empty:
            time.sleep(1)
            return
        self.p.send(self.topic, payload)

    def stop(self):
        super().stop()
        try:
            if self.p:
                self.p.flush()
                self.p.close()
        except Exception:
            pass
