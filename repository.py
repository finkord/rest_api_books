import uuid
from typing import List, Optional
from models import Book


class Repository:
    def __init__(self, db: List[Book]):
        self.db = db

    async def get_all(self) -> List[Book]:
        return self.db

    async def get_by_id(self, book_id: uuid.UUID) -> Optional[Book]:
        for book in self.db:
            if book.id == book_id:
                return book
        return None

    async def create(self, book: Book) -> Book:
        self.db.append(book)
        return book

    async def delete(self, book_id: uuid.UUID) -> bool:
        for i, book in enumerate(self.db):
            if book.id == book_id:
                self.db.pop(i)
                return True
        return False
