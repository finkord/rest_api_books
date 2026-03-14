import uuid
import base64
import json
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
        cursor: str | None = None
    ) -> dict:
        cursor_val = None
        cursor_id = None
        if cursor:
            try:
                decoded = base64.b64decode(cursor).decode("utf-8")
                cursor_data = json.loads(decoded)
                if "val" in cursor_data and "id" in cursor_data:
                    cursor_val = cursor_data["val"]
                    cursor_id = uuid.UUID(cursor_data["id"])
                elif "id" in cursor_data:
                    cursor_id = uuid.UUID(cursor_data["id"])
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid cursor format")

        items = await self.repository.get_all(
            status=status,
            author=author,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            cursor_val=cursor_val,
            cursor_id=cursor_id
        )

        next_cursor = None
        if len(items) > limit:
            # Drop the extra item fetched for peek
            last_item = items[limit - 1]
            items = items[:limit]
            
            cursor_dict = {"id": str(last_item.id)}
            if sort_by == "title":
                cursor_dict["val"] = last_item.title
            elif sort_by == "year_published":
                cursor_dict["val"] = last_item.year_published
                
            cursor_json = json.dumps(cursor_dict)
            next_cursor = base64.b64encode(cursor_json.encode("utf-8")).decode("utf-8")

        return {
            "items": items,
            "next_cursor": next_cursor
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
