from typing import List, Dict, Any
from fastapi import HTTPException
from app.schemas import BookRequest, BookQueryParams
from app.repository import Repository
from app.utils import build_pagination_links

class BookService:
    def __init__(self, repository: Repository):
        self.repository = repository

    async def get_books(self, params: BookQueryParams) -> dict:
        items, total = await self.repository.get_all(params)
        
        next_page, prev_page = build_pagination_links(
            base_url="/api/books",
            limit=params.limit,
            offset=params.offset,
            total=total,
            status=params.status,
            author=params.author,
            sort_by=params.sort_by,
            sort_order=params.sort_order
        )
            
        return {
            "items": items,
            "total": total,
            "limit": params.limit,
            "offset": params.offset,
            "next_page": next_page,
            "prev_page": prev_page
        }

    async def get_book(self, book_id: str) -> Dict[str, Any]:
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book

    async def create_books(self, books_request: List[BookRequest]) -> List[Dict[str, Any]]:
        if not books_request:
            return []
        books_dicts = [book.model_dump() for book in books_request]
        return await self.repository.create_many(books_dicts)

    async def delete_book(self, book_id: str) -> dict:
        deleted = await self.repository.delete(book_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"message": "Book deleted"}
