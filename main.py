from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import threading
import time
from fastapi import FastAPI
from dotenv import load_dotenv

from app.config import settings
from app.workers.kafka_producer_worker import KafkaProducerWorker
from app.workers.kafka_consumer_worker import KafkaConsumerWorker
from app.workers.sqs_consumer_worker import SqsConsumerWorker
from app.workers.sqs_producer_worker import SqsProducerWorker
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

load_dotenv()
from app.routers import router as all_routes
from app.controllers.device_controller import router as device_router
from logging_config import setup_logging
import logging
from app.models.base import Base
from app.sqs.lifespan import lifespan

setup_logging()
logger=logging.getLogger(__name__)

def handle_message(msg: dict):
    print(f"[{threading.current_thread().name}] Handled: {msg}")

# try:
#     app = FastAPI(lifespan=lifespan)
#     app.include_router(all_routes)

#     logger.info(" FastAPI app and routes initialized")
# except Exception as e:
#     logger.error(f" Error during app setup: {e}")
#     raise
if __name__ == "__main__":
    

    admin = KafkaAdminClient(bootstrap_servers=["localhost:9092"])
    try:
        admin.create_topics([NewTopic(name="topic", num_partitions=1, replication_factor=1)])
    except TopicAlreadyExistsError:
        pass
    finally:
        admin.close()
   
    consumerKafka=KafkaConsumerWorker("topic", "localhost:9092", "my-group", handler=handle_message)
    producerKafka=KafkaProducerWorker("topic","localhost:9092")

    # for i in range(5):
    #     producerKafka.source.put({"hello_kafka": i})

    sqsConsumer=SqsConsumerWorker(
            settings,
            queue_url="http://localhost:4566/000000000000/terminal-messages",
            region="us-east-1",
            handler=handle_message,
            wait_time_s=10,
            max_messages=10,
            endpoint_url="http://localhost:4566",
        )
    sqsProducer = SqsProducerWorker(
            queue_url="http://localhost:4566/000000000000/terminal-messages",
            region="us-east-1",
            endpoint_url="http://localhost:4566",
        )
# producer kafka, consumer kafka = init _kafka
    for i in range(10):
        sqsProducer.enqueue({"hello_sqs": i})

    workers = [
            consumerKafka,
            producerKafka,
            sqsConsumer,
            sqsProducer
        ]

    with ThreadPoolExecutor(max_workers=len(workers), thread_name_prefix="worker") as ex:
        futures = [ex.submit(w.run) for w in workers]
        try:
            print(" Workers started. Ctrl+C to stop.")
            # while True: pass
        except KeyboardInterrupt:
            print("\n[Main] Stop signal received.")
            for w in workers: w.stop()
            for f in as_completed(futures): f.result()
    print("[Main] All workers stopped.")

