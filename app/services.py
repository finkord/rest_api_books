import uuid
from urllib.parse import urlencode
from app.models import Book
from app.schemas import BookRequest
from app.repository import Repository
from app.exceptions import NotFoundError


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

        # Collect non-pagination filter params
        filter_params: dict = {}
        if status:
            filter_params["status"] = status
        if author:
            filter_params["author"] = author
        if sort_by:
            filter_params["sort_by"] = sort_by
        filter_params["sort_order"] = sort_order

        def _build_url(lim: int, off: int) -> str:
            params = {**filter_params, "limit": lim, "offset": off}
            return f"/api/books?{urlencode(params)}"

        next_page = None
        if offset + limit < total:
            next_page = _build_url(limit, offset + limit)

        prev_page = None
        if offset > 0:
            prev_page = _build_url(limit, max(0, offset - limit))

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
            raise NotFoundError("Book not found")
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
            raise NotFoundError("Book not found")
        return {"message": "Book deleted"}
