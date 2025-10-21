import json
import time
from typing import Callable, Optional
import logging
from kafka import KafkaConsumer
from kafka.structs import TopicPartition, OffsetAndMetadata
from app.workers.base_worker import BaseWorker
from logging_config import setup_logging
setup_logging()
logger=logging.getLogger(__name__)
class KafkaConsumerWorker(BaseWorker):
    """
    Consumes messages from a Kafka topic and calls a handler.
    Commits each record only after the handler succeeds (at-least-once).
    """

    def __init__(self, topic: str,server:str, group_id: str, handler: Callable[[dict], None]):
        """ Initialize the worker with Kafka connection details and a message handler """
        super().__init__(name=f"KafkaConsumer-{topic}")
        self.topic = topic
        self.server = server
        self.group_id = group_id
        self.handler = handler
        self.c: Optional[KafkaConsumer] = None

    def setup(self):
        """ Initialize the Kafka consumer """
        print(f"[{self.name}] Connecting to {self.server} topic '{self.topic}'...")
        self.c = KafkaConsumer(
            self.topic,
            bootstrap_servers=[self.server],
            group_id=self.group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        )

    def process(self):
        """ Poll for messages and process them """
        batches = self.c.poll(timeout_ms=1000) if self.c else {}
        records = [r for recs in batches.values() for r in recs]
        if not records:
            time.sleep(1)
            return

        for r in records:
            try:
                self.handler(r.value)
                tp = TopicPartition(r.topic, r.partition)
                self.c.commit({tp: OffsetAndMetadata(r.offset + 1, None)})
            except Exception:
                pass
            
    def stop(self):
        super().stop()
        try:
            if self.c:
                self.c.close()
        except Exception:
            pass
