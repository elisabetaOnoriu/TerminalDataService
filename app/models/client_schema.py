"""Schema for creating a new client."""

from pydantic import BaseModel, constr, ConfigDict

class ClientCreate(BaseModel):
    name:constr(min_length=1)

class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    client_id: int
    name: str
