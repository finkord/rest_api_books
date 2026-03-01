import uuid
from typing import List
from fastapi import APIRouter
from app.models import db
from app.schemas import BookRequest, BookResponse
from app.services import BookService
from app.repository import Repository

router = APIRouter(prefix="/api", tags=["Books"])
service = BookService(repository=Repository(db))


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/books", response_model=List[BookResponse])
async def get_books():
    return await service.get_books()


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: uuid.UUID):
    return await service.get_book(book_id)


@router.post("/books", status_code=201, response_model=BookResponse)
async def create_book(book: BookRequest):
    return await service.create_book(book)


@router.delete("/books/{book_id}")
async def delete_book(book_id: uuid.UUID):
    return await service.delete_book(book_id)
