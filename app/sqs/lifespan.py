from __future__ import annotations
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from connector import connect_to_sqs
from sqs_consumer import SQSConsumer

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan that starts/stops the SQS consumer.
    Uses connect_to_sqs
    """
    consumer: SQSConsumer | None = None

    queue_url = os.getenv("SQS_QUEUE_URL")

    if not connect_to_sqs(queue_url=queue_url):
        logger.warning("SQS_QUEUE_URL missing/invalid; consumer will not start.")
    else:
        consumer = SQSConsumer()
        await consumer.start()
        app.state.sqs_consumer = consumer

    try:
        yield
    finally:
        if consumer is not None:
            await consumer.shutdown()
