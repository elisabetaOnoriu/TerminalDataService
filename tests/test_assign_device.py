import pytest
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.client_model import Client
from app.models.device_model import Device

PATH_TMPL = "/client/clients/{client_id}/devices/{device_id}"


async def _mk_client(async_session: AsyncSession, name: str) -> Client:
    c = Client(name=name)
    async_session.add(c)
    await async_session.commit()
    await async_session.refresh(c)
    return c


async def _mk_device(
    async_session: AsyncSession,
    name: str,
    status: str = "CONNECTED",
    client_id: int | None = None,
    location: str | None = None,
    payload: str | None = None,
) -> Device:
    d = Device(
        name=name,
        status=status,
        client_id=client_id,
        location=location,
        payload=payload,
    )
    async_session.add(d)
    await async_session.commit()
    await async_session.refresh(d)
    return d


@pytest.mark.anyio
async def test_assign_device_idempotent_when_already_assigned(client, async_session: AsyncSession):
    """
    Verify that if the device is already assigned to the given client,
    the endpoint is idempotent and returns 200 with the unchanged device.
    """
    c = await _mk_client(async_session, "Client A")
    d = await _mk_device(async_session, name="Device A", client_id=c.client_id)

    path = PATH_TMPL.format(client_id=c.client_id, device_id=d.device_id)
    r: Response = await client.put(path)

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["device_id"] == d.device_id
    assert body["client_id"] == c.client_id


@pytest.mark.anyio
async def test_assign_device_conflict_when_assigned_to_other_client(client, async_session: AsyncSession):
    """
    Verify that assigning a device to a different client than the one it is already linked to
    returns 409 Conflict and includes a proper error message.
    """
    c1 = await _mk_client(async_session, "Client A")
    c2 = await _mk_client(async_session, "Client B")
    d = await _mk_device(async_session, name="Device B", client_id=c1.client_id)

    path = PATH_TMPL.format(client_id=c2.client_id, device_id=d.device_id)
    r: Response = await client.put(path)

    assert r.status_code == 409, r.text
    assert "already assigned" in r.json()["detail"].lower()


@pytest.mark.anyio
async def test_assign_device_404_when_client_not_found(client, async_session: AsyncSession):
    """
    Verify that assigning a device to a non-existent client
    returns 404 Not Found with 'Client not found' detail.
    """
    c = await _mk_client(async_session, "Existing Client")
    d = await _mk_device(async_session, name="Device C", client_id=c.client_id)

    missing_client_id = 999999
    path = PATH_TMPL.format(client_id=missing_client_id, device_id=d.device_id)
    r: Response = await client.put(path)

    assert r.status_code == 404, r.text
    assert r.json()["detail"].lower() == "client not found"


@pytest.mark.anyio
async def test_assign_device_404_when_device_not_found(client, async_session: AsyncSession):
    """
    Verify that assigning a non-existent device to an existing client
    returns 404 Not Found with 'Device not found' detail.
    """
    c = await _mk_client(async_session, "Client D")
    missing_device_id = 999999

    path = PATH_TMPL.format(client_id=c.client_id, device_id=missing_device_id)
    r: Response = await client.put(path)

    assert r.status_code == 404, r.text
    assert r.json()["detail"].lower() == "device not found"


@pytest.mark.anyio
async def test_assign_device_db_error_returns_500(client, async_session: AsyncSession, monkeypatch):
    """
    Verify that if a database error (SQLAlchemyError) occurs during the operation
    (e.g. while fetching the client or device), the endpoint responds with 500
    and the correct error detail message.
    """
    c = await _mk_client(async_session, "Client E")
    d = await _mk_device(async_session, name="Device E", client_id=c.client_id)

    async def boom_get(*args, **kwargs):
        raise SQLAlchemyError("simulated get failure")

    monkeypatch.setattr(async_session, "get", boom_get, raising=True)

    path = PATH_TMPL.format(client_id=c.client_id, device_id=d.device_id)
    r: Response = await client.put(path)

    assert r.status_code == 500, r.text
    assert "database error while assigning the device" in r.json()["detail"].lower()
