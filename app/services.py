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

    async def create_book(self, book_request: BookRequest) -> Dict[str, Any]:
        book_dict = book_request.model_dump()
        return await self.repository.create(book_dict)

    async def delete_book(self, book_id: str) -> dict:
        deleted = await self.repository.delete(book_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"message": "Book deleted"}
