import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas import BookRequest, BookResponse
from app.services import BookService
from app.repository import Repository
from app.database import get_db

router = APIRouter(prefix="/api", tags=["Books"])

async def get_service(db: AsyncIOMotorDatabase = Depends(get_db)):
    return BookService(repository=Repository(db))

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/books", response_model=List[BookResponse])
async def get_books(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: BookService = Depends(get_service),
):
    return await service.get_books(limit=limit, offset=offset)

@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, service: BookService = Depends(get_service)):
    return await service.get_book(book_id)

@router.post("/books", status_code=201, response_model=BookResponse)
async def create_book(book: BookRequest, service: BookService = Depends(get_service)):
    return await service.create_book(book)

@router.delete("/books/{book_id}")
async def delete_book(book_id: str, service: BookService = Depends(get_service)):
    return await service.delete_book(book_id)
