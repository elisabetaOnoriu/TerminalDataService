from typing import Optional

def connect_to_sqs(queue_url: str) -> bool:
    """
    Dummy connection checker for SQS. Does not perform any network call.
    Returns True if a non-empty queue_url is provided.
    """
    return bool(queue_url)
