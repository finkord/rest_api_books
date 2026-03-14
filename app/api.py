import uuid
from flask import request
from flask_restful import Resource
from pydantic import ValidationError

from app.models import SessionLocal, Book
from app.schemas import BookRequest, BookResponse, PaginatedBookResponse
from app.services import BookService
from app.repository import Repository


def _get_service():
    """Create a BookService with a fresh database session."""
    session = SessionLocal()
    return BookService(repository=Repository(session)), session


def _book_to_dict(book: Book) -> dict:
    """Convert a SQLAlchemy Book model instance to a serializable dict."""
    return {
        "id": str(book.id),
        "title": book.title,
        "author": book.author,
        "description": book.description,
        "status": book.status,
        "year_published": book.year_published,
    }


class HealthResource(Resource):
    def get(self):
        """
        Health check endpoint
        ---
        tags:
          - Health
        responses:
          200:
            description: Service is healthy
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: ok
        """
        return {"status": "ok"}, 200


class BookListResource(Resource):
    def get(self):
        """
        Get a paginated list of books
        ---
        tags:
          - Books
        parameters:
          - name: status
            in: query
            type: string
            enum: [available, borrowed]
            required: false
            description: Filter by status
          - name: author
            in: query
            type: string
            required: false
            description: Filter by author
          - name: sort_by
            in: query
            type: string
            enum: [title, year_published]
            required: false
            description: Sort by 'title' or 'year_published'
          - name: sort_order
            in: query
            type: string
            enum: [asc, desc]
            default: asc
            required: false
            description: "Sort order: 'asc' or 'desc'"
          - name: limit
            in: query
            type: integer
            default: 10
            minimum: 1
            maximum: 100
            required: false
            description: Number of items per page
          - name: offset
            in: query
            type: integer
            default: 0
            minimum: 0
            required: false
            description: Number of items to skip
        responses:
          200:
            description: A paginated list of books
            schema:
              type: object
              properties:
                items:
                  type: array
                  items:
                    $ref: '#/definitions/BookResponse'
                total:
                  type: integer
                limit:
                  type: integer
                offset:
                  type: integer
                next_page:
                  type: string
                  x-nullable: true
                prev_page:
                  type: string
                  x-nullable: true
        """
        service, session = _get_service()
        try:
            status = request.args.get("status")
            author = request.args.get("author")
            sort_by = request.args.get("sort_by")
            sort_order = request.args.get("sort_order", "asc")
            limit = request.args.get("limit", 10, type=int)
            offset = request.args.get("offset", 0, type=int)

            # Clamp limit and offset
            limit = max(1, min(limit, 100))
            offset = max(0, offset)

            result = service.get_books(
                status=status,
                author=author,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset,
            )

            # Serialize Book model instances inside items
            result["items"] = [_book_to_dict(book) for book in result["items"]]
            return result, 200
        finally:
            session.close()

    def post(self):
        """
        Create a new book
        ---
        tags:
          - Books
        parameters:
          - in: body
            name: body
            required: true
            schema:
              $ref: '#/definitions/BookRequest'
        responses:
          201:
            description: Book created successfully
            schema:
              $ref: '#/definitions/BookResponse'
          422:
            description: Validation error
        """
        service, session = _get_service()
        try:
            data = request.get_json(force=True)
            try:
                book_request = BookRequest(**data)
            except ValidationError as e:
                # Pydantic v2 ctx may contain non-serializable objects;
                # extract only JSON-safe fields from each error.
                errors = [
                    {"loc": err["loc"], "msg": err["msg"], "type": err["type"]}
                    for err in e.errors()
                ]
                return {"errors": errors}, 422

            book = service.create_book(book_request)
            return _book_to_dict(book), 201
        finally:
            session.close()


class BookResource(Resource):
    def get(self, book_id):
        """
        Get a book by ID
        ---
        tags:
          - Books
        parameters:
          - name: book_id
            in: path
            type: string
            format: uuid
            required: true
            description: The UUID of the book
        responses:
          200:
            description: A single book
            schema:
              $ref: '#/definitions/BookResponse'
          404:
            description: Book not found
        """
        service, session = _get_service()
        try:
            book_uuid = uuid.UUID(book_id)
            book = service.get_book(book_uuid)
            return _book_to_dict(book), 200
        except ValueError:
            return {"message": "Invalid book ID format"}, 400
        finally:
            session.close()

    def delete(self, book_id):
        """
        Delete a book by ID
        ---
        tags:
          - Books
        parameters:
          - name: book_id
            in: path
            type: string
            format: uuid
            required: true
            description: The UUID of the book to delete
        responses:
          200:
            description: Book deleted successfully
          404:
            description: Book not found
        """
        service, session = _get_service()
        try:
            book_uuid = uuid.UUID(book_id)
            result = service.delete_book(book_uuid)
            return result, 200
        except ValueError:
            return {"message": "Invalid book ID format"}, 400
        finally:
            session.close()
