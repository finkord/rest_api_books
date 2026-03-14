from pydantic import BaseModel, Field, field_validator
from fastapi import Query
import uuid
from datetime import datetime
from typing import Optional, Literal
from enum import Enum


class BookStatus(str, Enum):
    """Allowed states for a book's availability."""
    available = "available"
    borrowed = "borrowed"


class BookRequest(BaseModel):
    """Schema for book creation payloads."""
    
    title: str = Field(min_length=2, max_length=100)
    author: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=2, max_length=400)
    status: BookStatus
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
    """Schema for outgoing book payloads."""
    
    id: uuid.UUID
    title: str
    author: str
    description: str
    status: BookStatus
    year_published: int


class CursorPaginatedResponse(BaseModel):
    """Schema for cursor-based pagination response."""
    
    items: list[BookResponse]
    next_cursor: str | None = None


class BookQueryParams:
    """Encapsulates all query parameters for fetching books."""
    def __init__(
        self,
        status: Optional[BookStatus] = Query(None, description="Filter by status (available, borrowed)"),
        author: Optional[str] = Query(None, description="Filter by author"),
        sort_by: Optional[Literal["title", "year_published"]] = Query(None, description="Sort by 'title' or 'year_published'"),
        sort_order: Literal["asc", "desc"] = Query("asc", description="Sort order: 'asc' or 'desc'"),
        limit: int = Query(10, ge=1, le=100),
        cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    ):
        self.status = status
        self.author = author
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.limit = limit
        self.cursor = cursor
