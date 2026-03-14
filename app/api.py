from typing import List, Literal
from fastapi import APIRouter, Depends, Query
from app.schemas import BookRequest, BookResponse, PaginatedBookResponse, BookQueryParams
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
    params: BookQueryParams = Depends(),
    service: BookService = Depends(get_service),
):
    """
    Retrieve a paginated list of books.
    Supports filtering by status and author, and custom sorting.
    """
    return await service.get_books(params)


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, service: BookService = Depends(get_service)):
    return await service.get_book(book_id)


@router.post("/books", status_code=201, response_model=BookResponse)
async def create_book(book: BookRequest, service: BookService = Depends(get_service)):
    return await service.create_book(book)


@router.delete("/books/{book_id}")
async def delete_book(book_id: str, service: BookService = Depends(get_service)):
    return await service.delete_book(book_id)
