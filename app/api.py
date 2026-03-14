"""
API router definitions for the Book endpoints.
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import async_session
from app.schemas import BookRequest, BookResponse, CursorPaginatedResponse, BookQueryParams
from app.services import BookService
from app.repository import Repository

router = APIRouter(prefix="/api", tags=["Books"])


async def get_db():
    async with async_session() as session:
        yield session


async def get_service(db: AsyncSession = Depends(get_db)):
    return BookService(repository=Repository(db))


@router.get("/health")
async def health():
    """Check the health status of the API."""
    return {"status": "ok"}


@router.get("/books", response_model=CursorPaginatedResponse)
async def get_books(
    params: BookQueryParams = Depends(),
    service: BookService = Depends(get_service),
):
    """
    Retrieve a paginated list of books.
    Supports filtering by status and author, and custom sorting.
    """
    return await service.get_books(params)


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: uuid.UUID, service: BookService = Depends(get_service)):
    """Retrieve a single book by its UUID."""
    return await service.get_book(book_id)


@router.post("/books", status_code=201, response_model=List[BookResponse])
async def create_books(books: List[BookRequest], service: BookService = Depends(get_service)):
    """Bulk create multiple books."""
    return await service.create_books(books)


@router.delete("/books/{book_id}")
async def delete_book(book_id: uuid.UUID, service: BookService = Depends(get_service)):
    """Delete a single book by its UUID."""
    return await service.delete_book(book_id)
