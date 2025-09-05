"""Represents a client entity in the system."""
from __future__ import annotations

from sqlalchemy import  String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import List


class Client(Base):
    __tablename__ = "clients"

    client_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    devices: Mapped[list["Device"]] = relationship(
        "Device", back_populates="client"
    )
