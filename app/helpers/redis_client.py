import redis.asyncio as redis
from app.config.settings import get_settings

settings = get_settings()

async def get_redis() -> redis.Redis :
    """
    Create and return an async Redis client using the configured url
    """

    return redis.from_url(settings.REDIS_URL, decode_responses=True)

async def mirror_message_to_redis(r:redis.Redis, message_dict:dict)->None:
    """
    Push a new message into the Redis list and trim it to keep only the last N entries
    """
