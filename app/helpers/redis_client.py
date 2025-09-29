import json
import redis.asyncio as redis
from app.config.settings import get_settings

settings = get_settings()

async def get_redis() -> redis.Redis :
    """
    Create and return an async Redis client using the configured url
    """

    return redis.from_url(settings.REDIS_URL, decode_responses=True)

async def mirror_message_to_redis(r:redis.Redis, message:dict)->None:
    """
    Push a new message into the Redis list and trim it to keep only the last N entries
    """
    data = json.dumps(message, separators=(",", ":"))
    pipe = r.pipeline(transaction=True)
    pipe.lpush("latest:messages", data)
    pipe.ltrim("latest:messages",0, settings.REDIS_MAX_MESSAGES - 1)
    await pipe.execute()