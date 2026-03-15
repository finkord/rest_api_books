import uuid
from fastapi import HTTPException

from app.books.models import Book
from app.books.schemas import BookRequest, BooksPageResult
from app.auth.schemas import MessageResponse
from app.books.repository import BookRepository
from app.core.exceptions import NotFoundError

class BookService:
    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def get_books(
        self,
        status: str | None = None,
        author: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0
    ) -> BooksPageResult:
        items, total = await self.repository.get_all(
            status=status,
            author=author,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        return BooksPageResult(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )

    async def get_book(self, book_id: uuid.UUID) -> Book:
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise NotFoundError("Book not found")
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

    async def delete_book(self, book_id: uuid.UUID) -> MessageResponse:
        deleted = await self.repository.delete(book_id)
        if not deleted:
            raise NotFoundError("Book not found")
        return MessageResponse(message="Book deleted")
