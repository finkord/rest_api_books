from pydantic import BaseModel, Field, field_validator
import uuid
from datetime import datetime


class BookRequest(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    author: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=2, max_length=400)
    status: str = Field(min_length=2, max_length=40)
    year_published: int = Field(gt=0)

    @field_validator("title", "author", "description")
    @classmethod
    def check_not_empty(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("Field cannot consist only of whitespace")
        return value

    @field_validator("title")
    @classmethod
    def title_validator(cls, value: str) -> str:
        if value.startswith("_"):
            raise ValueError("Title cannot start with an underscore")
        return value

    @field_validator("status")
    @classmethod
    def status_validator(cls, value: str) -> str:
        allowed_statuses = {"available", "borrowed"}
        val_lower = value.strip().lower()
        if val_lower not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return val_lower

    @field_validator("year_published")
    @classmethod
    def check_year(cls, value: int) -> int:
        current_year = datetime.now().year
        if value > current_year:
            raise ValueError(
                f"Year published cannot be greater than the current year ({current_year})"
            )
        return value


class BookResponse(BaseModel):
    id: uuid.UUID
    title: str
    author: str
    description: str
    status: str
    year_published: int


class CursorPaginatedResponse(BaseModel):
    items: list[BookResponse]
    next_cursor: str | None = None
