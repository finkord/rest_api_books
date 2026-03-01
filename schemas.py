from pydantic import BaseModel, Field, field_validator
import uuid


class BookRequest(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    author: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=2, max_length=400)
    status: str = Field(min_length=2, max_length=40)
    year_published: int

    @field_validator("title")
    def title_validator(cls, value):
        if value.startswith("_"):
            raise ValueError("Title cannot start with an underscore")
        if value.strip() == "":
            raise ValueError("Title cannot be empty")
        return value


class BookResponse(BaseModel):
    id: uuid.UUID
    title: str
    author: str
    description: str
    status: str
    year_published: int
