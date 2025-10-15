"""Enumeration of possible device connection states."""

import enum

class Status(str, enum.Enum):
    """Enumeration of possible device connection states."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"
