import uuid
import urllib.parse
from typing import List
from app.models import Book
from app.schemas import BookRequest
from app.repository import Repository
from app.exceptions import NotFoundError


class BookService:
    def __init__(self, repository: Repository):
        self.repository = repository

    async def get_books(
        self,
        status: str | None = None,
        author: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0
    ) -> dict:
        items, total = await self.repository.get_all(
            status=status,
            author=author,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        # Build base URL to append query parameters easily
        base_url = "/api/books"
        
        base_params = {}
        if status: base_params["status"] = status
        if author: base_params["author"] = author
        if sort_by: base_params["sort_by"] = sort_by
        base_params["sort_order"] = sort_order
        
        next_page = None
        if offset + limit < total:
            next_params = {**base_params, "limit": limit, "offset": offset + limit}
            next_page = f"{base_url}?{urllib.parse.urlencode(next_params)}"

        prev_page = None
        if offset > 0:
            prev_offset = max(0, offset - limit)
            prev_params = {**base_params, "limit": limit, "offset": prev_offset}
            prev_page = f"{base_url}?{urllib.parse.urlencode(prev_params)}"
            
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "next_page": next_page,
            "prev_page": prev_page
        }

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

    async def delete_book(self, book_id: uuid.UUID) -> dict:
        deleted = await self.repository.delete(book_id)
        if not deleted:
            raise NotFoundError("Book not found")
        return {"message": "Book deleted"}
