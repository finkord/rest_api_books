import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import async_session
from app.schemas import BookRequest, BookResponse, PaginatedBookResponse
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
    return {"status": "ok"}


@router.get("/books", response_model=PaginatedBookResponse)
async def get_books(
    status: str | None = Query(None, description="Filter by status"),
    author: str | None = Query(None, description="Filter by author"),
    sort_by: str | None = Query(None, description="Sort by 'title' or 'year_published'"),
    sort_order: str = Query("asc", description="Sort order: 'asc' or 'desc'"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: BookService = Depends(get_service),
):
    return await service.get_books(
        status=status,
        author=author,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: uuid.UUID, service: BookService = Depends(get_service)):
    return await service.get_book(book_id)


@router.post("/books", status_code=201, response_model=BookResponse)
async def create_book(book: BookRequest, service: BookService = Depends(get_service)):
    return await service.create_book(book)


@router.delete("/books/{book_id}")
async def delete_book(book_id: uuid.UUID, service: BookService = Depends(get_service)):
    return await service.delete_book(book_id)
