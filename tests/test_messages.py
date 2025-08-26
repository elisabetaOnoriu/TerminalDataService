# tests/test_messages.py
import pytest
from datetime import datetime, timedelta, timezone
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.message_model import Message

PATH = "/messages"


async def _add_message(
    db: AsyncSession,
    ts: datetime,
    payload: str,
) -> Message:
    """
    Insert a message row using the async session and return it.
    """
    msg = Message(timestamp=ts, payload=payload)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg



@pytest.mark.anyio
async def test_get_messages_returns_empty_list_when_none_newer(client, async_session: AsyncSession):
    """
    When there are no messages newer than the provided timestamp, the endpoint returns 200 + [].
    """
    # choose a future cutoff to be sure we get an empty list
    cutoff = datetime.now(timezone.utc) + timedelta(days=365)
    r: Response = await client.get(PATH, params={"since": cutoff.isoformat().replace("+00:00", "Z")})
    assert r.status_code == 200, r.text
    assert r.json() == []


@pytest.mark.anyio
async def test_get_messages_returns_only_strictly_newer(client, async_session: AsyncSession):
    """
    Returns messages with timestamp strictly greater than the cutoff.
    Boundary check: one older, one exactly at cutoff, one newer.
    """
    t0 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    older = t0 - timedelta(seconds=1)
    equal = t0
    newer = t0 + timedelta(seconds=1)

    # seed data
    m1 = await _add_message(async_session, older, "older")
    m2 = await _add_message(async_session, equal, "equal")
    m3 = await _add_message(async_session, newer, "newer")

    r: Response = await client.get(PATH, params={"since": t0.isoformat().replace("+00:00", "Z")})
    assert r.status_code == 200, r.text

    items = r.json()
    # only the strictly newer one should be returned
    assert len(items) == 1
    assert items[0]["id"] == m3.id
    assert items[0]["payload"] == "newer"


@pytest.mark.anyio
async def test_get_messages_invalid_timestamp_returns_400(client):
    """
    Invalid ISO timestamp should return 400 with a clear error message.
    """
    r: Response = await client.get(PATH, params={"since": "not-a-date"})
    assert r.status_code == 400, r.text
    assert "invalid iso 8601" in r.json()["detail"].lower()


@pytest.mark.anyio
async def test_get_messages_db_error_returns_500(client, async_session: AsyncSession, monkeypatch):
    """
    Simulate a database error raised during execution and verify a 500 response.
    """
    async def boom(*args, **kwargs):
        raise SQLAlchemyError("simulated execute failure")

    monkeypatch.setattr(async_session, "execute", boom, raising=True)

    cutoff = datetime.now(timezone.utc)
    r: Response = await client.get(PATH, params={"since": cutoff.isoformat().replace("+00:00", "Z")})
    assert r.status_code == 500, r.text
    assert "database error while fetching messages" in r.json()["detail"].lower()
