"""
Async endpoints for retrieving messages from the database.

Accepts an ISO 8601 timestamp and returns all messages newer than that
timestamp as a JSON list (id, timestamp, payload).

Supports:
- pagination: limit, offset
- filters: device_id, from_ts/to_ts (ISO 8601; inclusive)

"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.helpers.database import get_db
from app.helpers.redis_client import get_redis, settings
from app.models.message_model import Message
from app.models.message_schema import MessageResponse, PaginatedMessages, LatestMessages

router = APIRouter()
logger = logging.getLogger(__name__)

def _parse_european_timestamp(ts: str) -> datetime:
    """
    Parsează DOAR formatele europene:
      - DD.MM.YYYY
      - DD.MM.YYYY HH:MM
      - DD.MM.YYYY HH:MM:SS

    Întoarce datetime timezone-aware (UTC).
    """
    if not isinstance(ts, str) or not ts.strip():
        raise HTTPException(status_code=400, detail="Missing timestamp")

    FALLBACK_FORMATS = (
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
    )

    for fmt in FALLBACK_FORMATS:
        try:
            dt = datetime.strptime(ts.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    raise HTTPException(
        status_code=400,
        detail="Invalid timestamp. Use format: DD.MM.YYYY[ HH:MM[:SS]] (e.g. 03.09.2025 14:30:00)",
    )


@router.get(
    "",
    response_model=PaginatedMessages,
    tags=["Messages"],
    summary="Get messages newer than a given timestamp",
    responses={
        200: {"description": "List of messages"},
        400: {"description": "Invalid timestamp"},
        500: {"description": "Database error while fetching messages"},
    },
)
async def get_messages(
    since: str = Query(..., description="Format: DD.MM.YYYY[ HH:MM:SS]"),
    device_id: Optional[int]=Query(None, description="Filter by device_id") ,
    limit: int = Query(50, ge=1, le=500, description="page size(1..500"),
    offset: int =Query(0, ge=0, description="Row offset"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedMessages:
    """
    Return all messages with `timestamp` strictly greater than the provided timestamp.
    """
    logger.info("Fetching messages since timestamp: %s", since)
    since_dt = _parse_european_timestamp(since)

    try:
        base_stmt = select(Message).where(Message.timestamp > since_dt).order_by(Message.timestamp)

        if device_id is not None:
            base_stmt=base_stmt.where(Message.device_id==device_id)

        total_querry=await db.execute(select(func.count()).select_from(base_stmt.subquery()))
        total=total_querry.scalar_one()

        paged_stmt = (
            base_stmt.order_by(Message.timestamp.asc())
            .offset(offset).limit(limit)
        )

        result = await db.execute(paged_stmt)
        rows = result.scalars().all()

        return PaginatedMessages(
            total=total,
            limit=limit,
            offset=offset,
            items=[MessageResponse.model_validate(m) for m in rows]
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error("Database error while fetching messages: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching messages",
        ) from e

@router.get(
    "/latest",
    tags=["Messages"],
    summary="Get the last N messages",
    response_model=LatestMessages,
    responses={
        200: {"description": "Success "},
        400: {"description": "Invalid request "},
        500: {"description": "Server error while reading from Redis"},
    },
)
async def get_latest_messages(
        limit: int = Query(
            default=None,
            ge=1,
            description=" Max items to return "
        ),
        r: redis.Redis = Depends(get_redis),
):
    "return the most recent mirrored messages from Redis"

    try:
        max_n = settings.REDIS_MAX_MESSAGES
        n= min(limit,max_n)

        redis_messages: List[str] = await r.lrange("latest:messages", 0, n-1)
        messages: List[Dict[str, Any]]=[json.loads(x) for x in redis_messages]

        return LatestMessages(
            count=len(messages),
            limit=n,
            items=messages,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch latest message {e}"
        )

