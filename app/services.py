from typing import List
from fastapi import HTTPException
from app.models import Book
from app.schemas import BookRequest
from app.repository import Repository


class BookService:
    def __init__(self, repository: Repository):
        self.repository = repository

    async def get_books(self, limit: int = 10, offset: int = 0) -> List[Book]:
        return await self.repository.get_all(limit=limit, offset=offset)

    async def get_book(self, book_id: str) -> Book:
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book

    async def create_book(self, book_request: BookRequest) -> Book:
        book = Book(
            title=book_request.title,
            author=book_request.author,
            description=book_request.description,
            status=book_request.status,
            year_published=book_request.year_published,
        )
        return await self.repository.create(book)

    async def delete_book(self, book_id: str) -> dict:
        deleted = await self.repository.delete(book_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"message": "Book deleted"}
