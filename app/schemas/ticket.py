from typing import Literal
from pydantic import BaseModel


class TicketCreate(BaseModel):
    title: str
    description: str
    category: Literal["Hardware", "Software", "Network", "Other"]
    priority: Literal["Low", "Medium", "High"]


class TicketResponse(BaseModel):
    title: str
    description: str
    category: str
    priority: str
