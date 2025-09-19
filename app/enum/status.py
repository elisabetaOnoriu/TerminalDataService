"""Enumeration of possible device connection states."""

import enum

class Status(str, enum.Enum):
    """enum """
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"
