from __future__ import annotations
import json
import asyncio
import logging
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import boto3
import xml.etree.ElementTree as ET
from botocore.config import Config as BotoConfig
from app.config.settings import Settings

logger = logging.getLogger(__name__)

class SQSConsumer:
    """
    Asynchronous SQS consumer
    - Polls SQS via boto3.receive_message (run in a thread to avoid blocking the event loop)
    - Dispatches each received message to a ThreadPoolExecutor worker (one thread per message)
    - Worker schedules async processing+deletion on the event loop
    - On success → delete_message; on failure → DO NOT delete (SQS redelivers after visibility timeout)

    """

    def __init__(self, settings: Settings) -> None:
        """
         Asynchronous SQS consumer
         - Polls SQS via boto3.receive_message (run in a thread to avoid blocking the event loop)
         - Dispatches each received message to a ThreadPoolExecutor worker (one thread per message)
         - Worker schedules async processing+deletion on the event loop
         - On success → delete_message; on failure → DO NOT delete (SQS redelivers after visibility timeout)

         """
        self.queue_url = str(settings.SQS_QUEUE_URL)
        self.poll_interval = settings.SQS_POLL_INTERVAL
        self.wait_time_seconds = settings.SQS_WAIT_TIME_SECONDS
        self.max_messages = settings.SQS_MAX_MESSAGES
        self.visibility_timeout = settings.SQS_VISIBILITY_TIMEOUT
        self.thread_pool_size = settings.SQS_THREAD_POOL_SIZE

        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop = asyncio.Event()
        self._executor = ThreadPoolExecutor(
            max_workers=self.thread_pool_size,
            thread_name_prefix="sqs-worker",
        )
        self._task = None

        self._sqs = boto3.client(
            "sqs",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.sqs_effective_endpoint,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=BotoConfig(retries={"max_attempts": 10, "mode": "standard"}),
        )

    async def start(self) -> None:
        """Start the polling loop."""
        self._loop = asyncio.get_running_loop()
        logger.info(
            "Starting SQS consumer for %s (poll=%ss, wait=%ss, max=%s, pool=%s, vis=%ss)",
            self.queue_url, self.poll_interval, self.wait_time_seconds,
            self.max_messages, self._executor._max_workers, self.visibility_timeout,
        )
        self._task = asyncio.create_task(self._run(), name="sqs-consumer-loop")

    async def shutdown(self) -> None:
        """Signal stop, wait for loop to finish, then drain the executor."""
        logger.info("Stopping SQS consumer...")
        self._stop.set()
        await asyncio.sleep(0.05)
        if self._task is not None:
            try:
                await self._task
            except Exception:
                logger.exception("SQS consumer loop raised during shutdown.")
        self._executor.shutdown(wait=True, cancel_futures=True)
        logger.info("SQS consumer stopped.")

    async def _run(self) -> None:
        """
        Main polling loop:
        - receive_message is blocking → run in default executor via run_in_executor(None, ...)
        - if no messages → sleep poll_interval
        - for each message → submit _handle_one_message to our worker pool
        """
        assert self._loop is not None, "Loop not initialized"
        while not self._stop.is_set():
            try:
                resp = await self._loop.run_in_executor(
                    None,
                    lambda: self._sqs.receive_message(
                        QueueUrl=self.queue_url,
                        MaxNumberOfMessages=self.max_messages,
                        WaitTimeSeconds=self.wait_time_seconds,
                        VisibilityTimeout=self.visibility_timeout,
                    ),
                 )
                messages = resp.get("Messages", [])
                if not messages:
                    await asyncio.sleep(self.poll_interval)
                    continue

                for msg in messages:
                    self._executor.submit(self._handle_one_message, msg)

            except Exception as exc:
                logger.exception("Error while polling SQS: %s", exc)
                await asyncio.sleep(min(5.0, self.poll_interval))

        logger.info("SQS consumer loop exited.")

    def _handle_one_message(self, msg: Dict[str, Any]) -> None:
        """
        Runs in a worker thread:
        - Parse body (JSON or raw)
        - Schedule async processing+deletion on the event loop
        - Wait for the result in THIS worker thread (does not block the event loop)
        """
        assert self._loop is not None, "Loop not initialized"

        receipt = msg.get("ReceiptHandle")
        body_str = msg.get("Body", "")

        if receipt is None:
            logger.warning("Received message without ReceiptHandle; skipping.")
            return

        try:
            body = json.loads(body_str)
        except json.JSONDecodeError:
            try:
                root = ET.fromstring(body_str)
                body = {"xml": body_str, "parsed": root}
            except ET.ParseError:
                body = {"raw": body_str}

        future = asyncio.run_coroutine_threadsafe(
            self._process_and_delete(body, receipt),
            self._loop,
        )
        try:
            future.result()
        except FutureTimeoutError as e:
            logger.error("Processing future timed out: %s", e)
        except Exception as e:
            logger.exception("Message processing failed; leaving it in the queue. Error: %s", e)

    async def _process_and_delete(self, body: Dict[str, Any], receipt: str) -> None:
        """
        Runs on the event loop:
        - Run business logic (_process_message)
        - On success → delete from SQS (blocking boto3 call run in a thread)
        - On error → re-raise (so worker does NOT delete and SQS will redeliver)
        """
        assert self._loop is not None, "Loop not initialized"
        await self._process_message(body)

        await self._loop.run_in_executor(
            None,
            lambda: self._sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt,
            ),
        )

    async def _process_message(self, body: Dict[str, Any]) -> None:
        """
        Dummy process logic
        """
        logger.info("Processed message: %s", body)
