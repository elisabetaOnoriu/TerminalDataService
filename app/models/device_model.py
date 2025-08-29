"""Represents a device entity in the system."""
from __future__ import annotations
from typing import Optional
from sqlalchemy import  Integer, String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.enum.status import Status


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clients.client_id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[Status] = mapped_column(
        SAEnum(Status, name="status_enum", native_enum=False),
        nullable=False,
        default=Status.DISCONNECTED,
    )
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    payload: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    client: Mapped["Client"] = relationship(
        "Client", back_populates="devices"
    )
