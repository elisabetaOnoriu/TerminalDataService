import pytest
from httpx import Response
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine
from main import app
from app.helpers.database import get_db

PATH = "/client/clients"

@pytest.mark.anyio
async def test_create_client_success(client):
    r: Response = await client.post(PATH, json={"name": "Acme Corp"})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["name"] == "Acme Corp"
    assert any(k.endswith("id") for k in data.keys())

@pytest.mark.anyio
async def test_create_client_duplicate_returns_409(client):
    payload = {"name": "Duplicate Co"}
    r1 = await client.post(PATH, json=payload)
    assert r1.status_code == 201, r1.text

    r2 = await client.post(PATH, json=payload)
    assert r2.status_code == 409, r2.text
    assert "detail" in r2.json()

@pytest.mark.anyio
async def test_create_client_validation_error_returns_422(client):
    r = await client.post(PATH, json={"name": ""})
    assert r.status_code == 422, r.text
    body = r.json()
    assert "detail" in body and isinstance(body["detail"], list)

    r2 = await client.post(PATH)
    assert r2.status_code == 422, r2.text

@pytest.mark.anyio
async def test_create_client_internal_error_returns_500(client, async_engine: AsyncEngine):
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession

    class BrokenSession(_AsyncSession):
        async def commit(self, *args, **kwargs):
            raise RuntimeError("Forced commit failure")

    broken_factory = async_sessionmaker(bind=async_engine, class_=BrokenSession, expire_on_commit=False)

    async def broken_get_db():
        async with broken_factory() as s:
            yield s

    prev_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = broken_get_db
    try:
        r = await client.post(PATH, json={"name": "Boom"})
        assert r.status_code == 500, r.text
        assert r.json().get("detail") == "Internal error while creating the client."
    finally:
        if prev_override is not None:
            app.dependency_overrides[get_db] = prev_override
        else:
            app.dependency_overrides.pop(get_db, None)
