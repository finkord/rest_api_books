from typing import List, Literal
from fastapi import APIRouter, Depends, Query
from app.schemas import BookRequest, BookResponse, PaginatedBookResponse
from app.services import BookService
from app.repository import Repository

router = APIRouter(prefix="/api", tags=["Books"])


async def get_service():
    return BookService(repository=Repository())


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/books", response_model=PaginatedBookResponse)
async def get_books(
    status: Literal["available", "borrowed"] | None = Query(None, description="Filter by status"),
    author: str | None = Query(None, description="Filter by author"),
    sort_by: Literal["title", "year_published"] | None = Query(None, description="Sort by 'title' or 'year_published'"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort order: 'asc' or 'desc'"),
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
async def get_book(book_id: str, service: BookService = Depends(get_service)):
    return await service.get_book(book_id)


@router.post("/books", status_code=201, response_model=BookResponse)
async def create_book(book: BookRequest, service: BookService = Depends(get_service)):
    return await service.create_book(book)


@router.delete("/books/{book_id}")
async def delete_book(book_id: str, service: BookService = Depends(get_service)):
    return await service.delete_book(book_id)
