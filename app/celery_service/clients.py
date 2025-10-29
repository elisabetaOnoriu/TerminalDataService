import os
import boto3
import redis
from app.config.settings import get_settings

settings = get_settings()

def get_sqs():
    return boto3.client(
        "sqs",
        region_name=str(settings.AWS_REGION),
        endpoint_url=str(settings.SQS_ENDPOINT_URL),
        aws_access_key_id=str(settings.AWS_ACCESS_KEY_ID),
        aws_secret_access_key=str(settings.AWS_SECRET_ACCESS_KEY),
    )

def get_redis():
    return redis.Redis(host="redis", port=6379, db=2)
    # return redis.Redis(host="localhost", port=6379, db=2)

