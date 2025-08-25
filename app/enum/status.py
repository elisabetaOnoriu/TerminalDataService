"""Enumeration of possible device connection states."""

import enum

class Status(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"
