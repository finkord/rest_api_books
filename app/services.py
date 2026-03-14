import uuid
from flask import abort
from app.models import Book
from app.schemas import BookRequest
from app.repository import Repository


class BookService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def get_books(
        self,
        status: str | None = None,
        author: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0
    ) -> dict:
        items, total = self.repository.get_all(
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

    def get_book(self, book_id: uuid.UUID) -> Book:
        book = self.repository.get_by_id(book_id)
        if not book:
            abort(404, description="Book not found")
        return book

    def create_book(self, book_request: BookRequest) -> Book:
        book = Book(
            title=book_request.title,
            author=book_request.author,
            description=book_request.description,
            status=book_request.status,
            year_published=book_request.year_published,
        )
        return self.repository.create(book)

    def delete_book(self, book_id: uuid.UUID) -> dict:
        deleted = self.repository.delete(book_id)
        if not deleted:
            abort(404, description="Book not found")
        return {"message": "Book deleted"}
