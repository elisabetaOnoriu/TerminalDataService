# tests/test_sqs_consumer_env_driven.py
import asyncio
import json
import logging
import uuid

import boto3
import pytest
from moto import mock_aws

from app.sqs.sqs_consumer import SQSConsumer


@pytest.fixture(autouse=True)
def _quiet_logs():
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


@pytest.fixture
def region():
    return "us-east-1"


@pytest.fixture
def moto_sqs(region):
    with mock_aws():
        yield boto3.client("sqs", region_name=region)


@pytest.fixture
def queue_url(moto_sqs):
    name = f"test-queue-{uuid.uuid4().hex}"
    return moto_sqs.create_queue(QueueName=name)["QueueUrl"]


@pytest.fixture
def env_config(monkeypatch, queue_url, region):
    """
    Configure environment variables expected by SQSConsumer.__init__.
    """
    monkeypatch.setenv("SQS_QUEUE_URL", queue_url)
    monkeypatch.setenv("SQS_POLL_INTERVAL", "0.05")
    monkeypatch.setenv("SQS_WAIT_TIME_SECONDS", "1")
    monkeypatch.setenv("SQS_MAX_MESSAGES", "10")
    monkeypatch.setenv("SQS_THREAD_POOL_SIZE", "2")
    monkeypatch.setenv("SQS_VISIBILITY_TIMEOUT", "5")
    monkeypatch.setenv("AWS_REGION", region)
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)


@pytest.mark.asyncio
async def test_process_and_delete_success(moto_sqs, queue_url, env_config, monkeypatch):
    """
    Verifies that one or more messages are polled, processed, and deleted.
    """
    moto_sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps({"ok": 1}))
    moto_sqs.send_message(QueueUrl=queue_url, MessageBody="raw-body")

    processed = []

    async def fake_process(self, body):
        processed.append(body)

    monkeypatch.setattr(SQSConsumer, "_process_message", fake_process, raising=True)

    consumer = SQSConsumer()
    await consumer.start()
    await asyncio.sleep(0.8)
    await consumer.shutdown()

    attrs = moto_sqs.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"]
    )["Attributes"]
    assert attrs["ApproximateNumberOfMessages"] == "0"
    assert len(processed) == 2



@pytest.mark.asyncio
async def test_graceful_shutdown(moto_sqs, queue_url, env_config, monkeypatch):
    """
    Verifies the consumer shuts down cleanly while tasks are in flight.
    """
    for i in range(5):
        moto_sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps({"i": i}))

    seen = []

    async def slow(self, body):
        seen.append(body)
        await asyncio.sleep(0.1)

    monkeypatch.setattr(SQSConsumer, "_process_message", slow, raising=True)

    consumer = SQSConsumer()
    await consumer.start()
    await asyncio.sleep(0.3)
    await consumer.shutdown()

    assert len(seen) >= 1
