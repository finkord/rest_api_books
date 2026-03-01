import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Book


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self, limit: int = 10, cursor: Optional[uuid.UUID] = None
    ) -> List[Book]:
        stmt = select(Book).order_by(Book.id).limit(limit)

        if cursor:
            stmt = stmt.where(Book.id > cursor)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, book_id: uuid.UUID) -> Optional[Book]:
        result = await self.session.execute(select(Book).where(Book.id == book_id))
        return result.scalars().first()

    async def create(self, book: Book) -> Book:
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def delete(self, book_id: uuid.UUID) -> bool:
        book = await self.get_by_id(book_id)
        if book:
            await self.session.delete(book)
            await self.session.commit()
            return True
        return False
