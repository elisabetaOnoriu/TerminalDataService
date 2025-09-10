import json
import pytest
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.client_model import Client

PATH = "/devices/devices"


async def _mk_client(async_session: AsyncSession, name: str) -> Client:
    """
    Create and persist a client row directly in the test DB.
    """
    c = Client(name=name)
    async_session.add(c)
    await async_session.commit()
    await async_session.refresh(c)
    return c


@pytest.mark.anyio
async def test_create_device_success_minimal(client, async_session: AsyncSession):
    c = await _mk_client(async_session, "Client for minimal device")
    payload = {
        "name": "Device One",
        "status": "connected",
        "client_id": c.client_id,
    }
    r: Response = await client.post(PATH, json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == payload["name"]
    assert body["status"] == "connected"
    assert body["client_id"] == c.client_id
    assert "location" in body
    assert "payload" in body


@pytest.mark.anyio
async def test_create_device_serializes_payload_dict(client, async_session: AsyncSession):
    """
    When payload is provided as a JSON string (schema only accepts str),
    the endpoint should store and return it correctly.
    """
    c = await _mk_client(async_session, "Client for payload dict")

    raw_payload = {"a": 1, "b": {"c": True}}
    payload = {
        "name": "Device With Dict Payload",
        "status": "connected",
        "client_id": c.client_id,
        "payload": json.dumps(raw_payload),
    }

    r: Response = await client.post(PATH, json=payload)
    assert r.status_code == 201, r.text

    body = r.json()
    assert isinstance(body["payload"], str)
    assert json.loads(body["payload"]) == raw_payload


@pytest.mark.anyio
async def test_create_device_invalid_payload_returns_422(client, async_session: AsyncSession):
    """
    If payload is not a string (e.g., dict), Pydantic should reject it with 422 Unprocessable Entity.
    """
    c = await _mk_client(async_session, "Client for 422 payload")

    bad_payload = {"bad": "dict instead of string"}

    payload = {
        "name": "Device Bad Payload",
        "status": "connected",
        "client_id": c.client_id,
        "payload": bad_payload,
    }

    r: Response = await client.post(PATH, json=payload)
    assert r.status_code == 422, r.text
    body = r.json()
    assert "payload" in str(body["detail"]).lower()



@pytest.mark.anyio
async def test_create_device_validation_error_422_missing_name(client, async_session: AsyncSession):
    c = await _mk_client(async_session, "Client for 422")
    payload = {
        "status": "connected",
        "client_id": c.client_id,
    }
    r: Response = await client.post(PATH, json=payload)
    assert r.status_code == 422, r.text
    err = r.json()
    assert err["detail"] and isinstance(err["detail"], list)


@pytest.mark.anyio
async def test_create_device_db_error_returns_500(client, async_session: AsyncSession, monkeypatch):
    c = await _mk_client(async_session, "Client for 500")
    payload = {
        "name": "Device Boom",
        "status": "connected",
        "client_id": c.client_id,
    }
    from sqlalchemy.exc import SQLAlchemyError
    async def boom(*args, **kwargs):
        raise SQLAlchemyError("simulated commit failure")
    monkeypatch.setattr(async_session, "commit", boom, raising=True)

    r: Response = await client.post(PATH, json=payload)
    assert r.status_code == 500, r.text
    assert "database error while creating the device" in r.json()["detail"].lower()
