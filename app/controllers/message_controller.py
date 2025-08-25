"""
This module defines the endpoint for retrieving messages stored in the database.
The endpoint accepts a timestamp (ISO 8601 format) and returns all messages
newer than that timestamp as a JSON list. Each message includes ID, timestamp,
and the raw payload.

"""

import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.helpers.database import get_db
from app.models.message_model import Message
from app.models.message_schema import MessageResponse

router = APIRouter()
logger = logging.getLogger(__name__)

def _parse_iso_timestamp(ts: str) -> datetime:
    """
    Parses an ISO 8601 timestamp string into a timezone-aware datetime object.
    If the string ends with 'Z', it's interpreted as UTC.

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

@router.get("", response_model=List[MessageResponse], tags=["Messages"])
def get_messages(
    since: str = Query(..., description="ISO 8601 UTC timestamp"),
    db: Session = Depends(get_db)
) -> List[MessageResponse]:
    """
    Returns all messages newer than the given ISO 8601 timestamp.

    """
    logger.info("Fetching messages since timestamp: %s", since)
    since_dt = _parse_iso_timestamp(since)

    messages = (
        db.query(Message)
        .filter(Message.timestamp > since_dt)
        .order_by(Message.timestamp)
        .all()
    )

    if not messages:
        logger.info("No messages found after %s", since_dt)
        return []

    logger.info("Found %d messages after %s", len(messages), since_dt)
    return messages
