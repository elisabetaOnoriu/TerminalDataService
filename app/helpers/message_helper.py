from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message_model import Message

async def save_message(
    session: AsyncSession,
    *,
    summary,
) -> Message:
    """  Save a message into the database. """
    msg = Message(
        device_id=int(summary.device_id),
        client_id=int(summary.client_id),
        sensor=summary.sensor or None,
        value=summary.value or None,
        unit=summary.unit or None,
        payload="saved from consumer"

    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg
