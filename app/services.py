"""
Service layer containing the business logic for Book entities.
"""
from fastapi import HTTPException
import uuid
from typing import List
from app.models import Book
from app.schemas import BookRequest, BookQueryParams
from app.repository import Repository
from app.utils import decode_cursor, encode_cursor


class BookService:
    """Service class abstracting business logic for the Book API endpoints."""
    
    def __init__(self, repository: Repository):
        self.repository = repository

    async def get_books(self, params: BookQueryParams) -> dict:
        cursor_val, cursor_id = None, None
        if params.cursor:
            cursor_val, cursor_id = decode_cursor(params.cursor)
            if cursor_val is None and cursor_id is None:
                raise HTTPException(status_code=400, detail="Invalid cursor format")

        items = await self.repository.get_all(params, cursor_val, cursor_id)

        next_cursor = None
        if len(items) > params.limit:
            # Drop the extra item fetched for peek
            last_item = items[params.limit - 1]
            items = items[:params.limit]
            
            sort_val = None
            if params.sort_by == "title":
                sort_val = last_item.title
            elif params.sort_by == "year_published":
                sort_val = last_item.year_published
                
            next_cursor = encode_cursor(last_item.id, params.sort_by, sort_val)

        return {
            "items": items,
            "next_cursor": next_cursor
        }

    async def get_book(self, book_id: uuid.UUID) -> Book:
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book

    async def create_books(self, book_requests: List[BookRequest]) -> List[Book]:
        books = [
            Book(
                title=req.title,
                author=req.author,
                description=req.description,
                status=req.status,
                year_published=req.year_published,
            )
            for req in book_requests
        ]
        return await self.repository.create_many(books)

    async def delete_book(self, book_id: uuid.UUID) -> dict:
        deleted = await self.repository.delete(book_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"message": "Book deleted"}
