import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc, func
from app.models import Book


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[Book], int]:
        query = select(Book)
        
        if status:
            query = query.where(Book.status == status)
        if author:
            query = query.where(Book.author == author)
            
        if sort_by == "title":
            order_func = desc(Book.title) if sort_order == "desc" else asc(Book.title)
            query = query.order_by(order_func)
        elif sort_by == "year_published":
            order_func = desc(Book.year_published) if sort_order == "desc" else asc(Book.year_published)
            query = query.order_by(order_func)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total_count = total_result.scalar_one()

        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all()), total_count

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
