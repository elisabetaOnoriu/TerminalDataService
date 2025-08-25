"""Represents a device entity in the system."""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as Enum
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.enum.status import Status


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False)
    name=Column(String, nullable=False)
    status = Column(Enum(Status), default=Status.DISCONNECTED, nullable=False)
    location = Column(String, nullable=True)
    payload = Column(String, nullable=True)

    client=relationship("Client", back_populates="devices")
