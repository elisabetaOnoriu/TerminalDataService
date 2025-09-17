"""
    Schema used for serializing Message objects returned by the API.

    This model defines the structure of a message as it will appear
    in the JSON response. It is typically used as a response model
    in the `/messages` endpoint.

"""
from datetime import datetime
from typing import List
from pydantic import BaseModel

class MessageResponse(BaseModel):
    id: int
    device_id:int
    timestamp: datetime
    payload: str

    model_config = {
        "from_attributes": True
    }


class PaginatedMessages(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[MessageResponse]