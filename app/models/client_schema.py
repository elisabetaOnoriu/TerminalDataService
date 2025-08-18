from pydantic import BaseModel, constr
from typing import Optional
class ClientCreate(BaseModel):
    name:constr(min_length=1)