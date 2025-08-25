"""Represents a client entity in the system."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class Client(Base):
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True )
    name=Column(String, nullable=False)

    devices=relationship("Device", back_populates="client")
