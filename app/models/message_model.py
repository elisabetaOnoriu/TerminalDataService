"""Represents a message entity in the system."""
from __future__ import annotations
from sqlalchemy import Column, Integer, DateTime,Text, text
from app.models.base import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    payload = Column(Text, nullable=False)
