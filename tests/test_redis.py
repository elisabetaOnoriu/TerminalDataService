import asyncio
from app.helpers.redis_client import get_redis, mirror_message_to_redis

async def _t():
    r = await get_redis()
    await mirror_message_to_redis(r, {"hello": "world"})
    print(await r.lrange("monitoring:messages:latest", 0, 0))

asyncio.run(_t())
