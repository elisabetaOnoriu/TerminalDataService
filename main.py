from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import threading
import time
from fastapi import FastAPI
from dotenv import load_dotenv

from app.workers.init_workers import init_kafka, init_sqs
from app.celery_service.run import start_beat, start_worker

load_dotenv()
from app.routers import router as all_routes
from app.controllers.device_controller import router as device_router
from logging_config import setup_logging
import logging
from app.models.base import Base
from app.sqs.lifespan import lifespan

setup_logging()
logger=logging.getLogger(__name__)

if __name__ == "__main__":
   
    worker = start_worker()
    beat = start_beat()
    
    worker.wait()
    beat.wait()
   
    # producerKafka,consumerKafka=init_kafka()
    # sqsProducer,sqsConsumer=init_sqs()
    # workers = [
    #         producerKafka,
    #         sqsProducer,
    #         consumerKafka,
    #         sqsConsumer
    #     ]

    # with ThreadPoolExecutor(max_workers=len(workers), thread_name_prefix="worker") as ex:
    #     futures = [ex.submit(w.run) for w in workers]
    #     try:
    #         print(" Workers started. Ctrl+C to stop.")
    #     except KeyboardInterrupt:
    #         print("\n[Main] Stop signal received.")
    #         for w in workers: w.stop()
    #         for f in as_completed(futures): f.result()
    # print("[Main] All workers stopped.")
