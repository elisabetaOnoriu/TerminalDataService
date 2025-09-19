"""Schema for creating a new device."""
from typing import Optional, Any
from pydantic import BaseModel, constr, ConfigDict
from app.enum.status import Status


class DeviceCreate(BaseModel):
    client_id: int
    status: Optional[Status] = Status.DISCONNECTED
    name: constr(min_length=1)
    location: Optional[str] = None
    payload: Optional[str] = None

class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    device_id: int
    client_id: int | None = None
    name: str
    status: str
    location: str | None = None
    payload: str| None = None
