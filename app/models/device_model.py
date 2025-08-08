from sqlalchemy import Column, Integer, String, ForeignKey, Enum as Enum
from app.models.Base import Base
from app.models.Status import Status

class Device(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False)
    status = Column(Enum(Status), default=Status.DISCONNECTED, nullable=False)
    location = Column(String, nullable=True)
    payload = Column(String, nullable=True)
