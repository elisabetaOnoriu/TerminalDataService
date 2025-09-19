# app/sqs/lifespan.py
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config.settings import get_settings
from app.sqs.connector import connect_to_sqs
from app.sqs.sqs_consumer import SQSConsumer
from app.helpers.database import SessionLocal

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    consumer: SQSConsumer | None = None

    if not connect_to_sqs(queue_url=str(settings.SQS_QUEUE_URL)):
        logger.warning("SQS_QUEUE_URL missing/invalid; consumer will not start.")
    else:
        consumer = SQSConsumer(settings, SessionLocal)
        await consumer.start()
        app.state.sqs_consumer = consumer

    try:
        yield
    finally:
        if consumer is not None:
            await consumer.shutdown()
