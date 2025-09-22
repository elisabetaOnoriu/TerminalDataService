from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.client_model import Client
from app.models.device_model import Device
from app.enum.status import Status

async def ensure_client(session: AsyncSession, client_id: int) -> Client:
    """Return client if exists, else create it."""
    res = await session.execute(select(Client).where(Client.client_id == client_id))
    c = res.scalar_one_or_none()
    if c:
        return c

    c = Client(client_id=client_id, name=f"AUTO-{client_id}")
    session.add(c)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        res = await session.execute(select(Client).where(Client.client_id == client_id))
        c = res.scalar_one()
    return c

async def ensure_device(session: AsyncSession, device_id: int, client_id: int) -> Device:
    """Return device if exists, else ensure client and create it."""
    res = await session.execute(select(Device).where(Device.device_id == device_id))
    d = res.scalar_one_or_none()
    if d:
        return d

    await ensure_client(session, client_id)

    d = Device(
        device_id=device_id,
        client_id=client_id,
        name=f"AUTO-{device_id}",
        status=Status.DISCONNECTED,
    )
    session.add(d)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        res = await session.execute(select(Device).where(Device.device_id == device_id))
        d = res.scalar_one()
    return d
