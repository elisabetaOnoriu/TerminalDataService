from pydantic import BaseModel
from typing import Optional
from app.models.Status import Status

class DeviceCreate(BaseModel):
    client_id: int
    status: Optional[Status] = Status.DISCONNECTED
    location: Optional[str] = None
    payload: Optional[str] = None
