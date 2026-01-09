import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import router as all_routes
from app.controllers.device_controller import router as device_router
from logging_config import setup_logging
import logging
from app.sqs.lifespan import lifespan
from pyctuator.pyctuator import Pyctuator


load_dotenv()
# import queue
# from app.models.base import Base
# import threading
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import time
# from app.workers.init_workers import init_kafka, init_sqs
#from app.celery_service.run import spawn


setup_logging()
logger=logging.getLogger(__name__)

app = FastAPI(lifespan=lifespan)
app.include_router(all_routes)

Pyctuator(
    app,
    app_name="Terminal Data Service",
    app_url="http://localhost:8000",
    pyctuator_endpoint_url="http://localhost:8000/actuator",
    registration_url=None
    )


if __name__ == "__main__":

    uvicorn.run("main:app", host="0.0.0.0", port=8000)

    # worker = spawn("worker", concurrency=4)
    # beat = spawn("beat")
    # worker.wait()
    # beat.wait()
   
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
    print("[Main] All workers stopped.")
