import uuid
from pydantic import BaseModel, Field

class Book(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    author: str
    description: str
    status: str
    year_published: int
