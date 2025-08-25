"""
    Schema used for serializing Message objects returned by the API.

    This model defines the structure of a message as it will appear
    in the JSON response. It is typically used as a response model
    in the `/messages` endpoint.

"""
from datetime import datetime
from pydantic import BaseModel

class MessageResponse(BaseModel):
    id: int
    timestamp: datetime
    payload: str

    class Config:
        orm_mode = True
