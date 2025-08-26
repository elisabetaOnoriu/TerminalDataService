"""
Async endpoints for retrieving messages from the database.

Accepts an ISO 8601 timestamp and returns all messages newer than that
timestamp as a JSON list (id, timestamp, payload).
"""

import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.database import get_db
from app.models.message_model import Message
from app.models.message_schema import MessageResponse

router = APIRouter()
logger = logging.getLogger(__name__)

def _parse_iso_timestamp(ts: str) -> datetime:
    """
    Parse an ISO 8601 timestamp into a timezone-aware datetime (UTC by default).
    If the string ends with 'Z', treat it as UTC. If it has no tzinfo, assume UTC.
    """
    try:
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as exc:
        logger.warning("Invalid ISO timestamp format received: %s", ts)
        raise HTTPException(status_code=400, detail="Invalid ISO 8601 timestamp") from exc


@router.get(
    "",
    response_model=List[MessageResponse],
    tags=["Messages"],
    summary="Get messages newer than a given timestamp",
    responses={
        200: {"description": "List of messages"},
        400: {"description": "Invalid timestamp"},
        500: {"description": "Database error while fetching messages"},
    },
)
async def get_messages(
    since: str = Query(..., description="ISO 8601 UTC timestamp"),
    db: AsyncSession = Depends(get_db),
) -> List[MessageResponse]:
    """
    Return all messages with `timestamp` strictly greater than the provided ISO 8601 timestamp.
    """
    logger.info("Fetching messages since timestamp: %s", since)
    since_dt = _parse_iso_timestamp(since)

    try:
        stmt = (
            select(Message)
            .where(Message.timestamp > since_dt)
            .order_by(Message.timestamp)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            logger.info("No messages found after %s", since_dt)
            return []

        logger.info("Found %d messages after %s", len(rows), since_dt)
        return [
            MessageResponse(id=m.id, timestamp=m.timestamp, payload=m.payload)
            for m in rows
        ]

    except SQLAlchemyError as e:
        logger.error("Database error while fetching messages: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching messages",
        ) from e
