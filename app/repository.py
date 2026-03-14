import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc, or_, and_
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
        cursor_val: Optional[str | int] = None,
        cursor_id: Optional[uuid.UUID] = None
    ) -> List[Book]:
        query = select(Book)
        
        if status:
            query = query.where(Book.status == status)
        if author:
            query = query.where(Book.author == author)
            
        # Select the column to sort by
        sort_col = Book.title if sort_by == "title" else Book.year_published if sort_by == "year_published" else None
        
        # Apply cursor logic if cursor provided
        if cursor_val is not None and cursor_id is not None and sort_col is not None:
            if sort_order == "desc":
                query = query.where(
                    or_(
                        sort_col < cursor_val,
                        and_(sort_col == cursor_val, Book.id < cursor_id)
                    )
                )
            else:
                query = query.where(
                    or_(
                        sort_col > cursor_val,
                        and_(sort_col == cursor_val, Book.id > cursor_id)
                    )
                )
        elif cursor_val is None and cursor_id is not None and sort_col is None:
            # Fallback if no sort_by is specified (sorting just by ID or relying on DB default, but we should force ID sort)
            pass

        # Apply deterministic sorting
        if sort_col is not None:
            if sort_order == "desc":
                query = query.order_by(desc(sort_col), desc(Book.id))
            else:
                query = query.order_by(asc(sort_col), asc(Book.id))
        else:
             query = query.order_by(asc(Book.id))
             if cursor_id is not None:
                 query = query.where(Book.id > cursor_id)

        # Fetch limit + 1 items to know if there's a next page
        result = await self.session.execute(query.limit(limit + 1))
        return list(result.scalars().all())

    async def get_by_id(self, book_id: uuid.UUID) -> Optional[Book]:
        result = await self.session.execute(select(Book).where(Book.id == book_id))
        return result.scalars().first()

    async def create(self, book: Book) -> Book:
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def create_many(self, books: List[Book]) -> List[Book]:
        self.session.add_all(books)
        await self.session.commit()
        for book in books:
            await self.session.refresh(book)
        return books

    async def delete(self, book_id: uuid.UUID) -> bool:
        book = await self.get_by_id(book_id)
        if book:
            await self.session.delete(book)
            await self.session.commit()
            return True
        return False
