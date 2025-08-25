import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from app.config.settings import get_settings

load_dotenv()
settings = get_settings()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sqs-consumer")

# SQS Client via boto3 session
session = boto3.session.Session(
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)
sqs = session.client("sqs", endpoint_url=settings.sqs_effective_endpoint)

# Resolve Queue URL dynamically
def _queue_url() -> str:
    return settings.queue_url or sqs.get_queue_url(QueueName=settings.QUEUE_NAME)["QueueUrl"]

QUEUE_URL = _queue_url()
POLL_INTERVAL = int(os.getenv("SQS_POLL_INTERVAL", 5))  # seconds
THREAD_POOL_SIZE = int(os.getenv("SQS_THREAD_POOL_SIZE", 4))
MAX_MESSAGES = int(os.getenv("SQS_MAX_MESSAGES", 10))
WAIT_TIME = int(os.getenv("SQS_WAIT_TIME", 10))


# Message Processor
def process_message(message):
    try:
        body = message["Body"]
        logger.info(f"Processing message ID={message['MessageId']}, Body={body}")

        # Simulate message processing
        time.sleep(1)

        # Delete message from queue after successful processing
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])
        logger.info(f"Deleted message ID={message['MessageId']}")

    except Exception as e:
        logger.error(f"Error processing message {message.get('MessageId', 'UNKNOWN')}: {e}")


# Polling Loop
def poll_sqs():
    logger.info("SQS consumer started")
    executor = ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE)

    try:
        while True:
            try:
                response = sqs.receive_message(
                    QueueUrl=QUEUE_URL,
                    MaxNumberOfMessages=MAX_MESSAGES,
                    WaitTimeSeconds=WAIT_TIME
                )
                messages = response.get("Messages", [])

                if messages:
                    logger.info(f"Received {len(messages)} messages from queue")
                    for msg in messages:
                        executor.submit(process_message, msg)
                else:
                    logger.debug("No messages received")

            except (BotoCoreError, ClientError) as e:
                logger.error(f"SQS error: {e}")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
    finally:
        executor.shutdown(wait=True)


if __name__ == "__main__":
    if not QUEUE_URL:
        logger.error("Missing required SQS queue URL")
    else:
        poll_sqs()
