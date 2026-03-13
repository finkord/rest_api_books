import uuid
from typing import List
from fastapi import HTTPException
from app.models import Book
from app.schemas import BookRequest
from app.repository import Repository


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
        params = []
        if status: params.append(f"status={status}")
        if author: params.append(f"author={author}")
        if sort_by: params.append(f"sort_by={sort_by}")
        params.append(f"sort_order={sort_order}")
        
        base_query = "&".join(params)
        base_query = f"?{base_query}&" if base_query else "?"

        next_page = None
        if offset + limit < total:
            next_page = f"{base_url}{base_query}limit={limit}&offset={offset + limit}"

        prev_page = None
        if offset > 0:
            prev_offset = max(0, offset - limit)
            prev_page = f"{base_url}{base_query}limit={limit}&offset={prev_offset}"
            
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

    async def delete_book(self, book_id: uuid.UUID) -> dict:
        deleted = await self.repository.delete(book_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"message": "Book deleted"}
