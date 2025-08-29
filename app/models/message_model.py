"""Represents a message entity in the system."""
from __future__ import annotations
from sqlalchemy import  DateTime,Text, text
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    payload: Mapped[str] = mapped_column(Text, nullable=False)
