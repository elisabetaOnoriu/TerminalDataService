"""Represents a message entity in the system."""
from __future__ import annotations
from sqlalchemy import DateTime, Text, text, Integer, ForeignKey
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    client_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    sensor: Mapped[str] = mapped_column(Text, nullable=True)
    value: Mapped[str] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(Text, nullable=True)
    timestamp: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    payload: Mapped[str] = mapped_column(Text, nullable=False)
