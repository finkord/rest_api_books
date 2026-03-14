"""
Repository layer handling all interactions with the database.
"""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc, or_, and_, Select
from app.models import Book
from app.schemas import BookQueryParams


class Repository:
    """Data access abstraction for Book entities over SQLAlchemy AsyncSession."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        params: BookQueryParams,
        cursor_val: Optional[str | int] = None,
        cursor_id: Optional[uuid.UUID] = None
    ) -> List[Book]:
        query = select(Book)
        
        query = self._apply_filters(query, params)
        sort_col = self._get_sort_column(params.sort_by)
        
        if cursor_id is not None:
             query = self._apply_cursor(query, sort_col, params.sort_order, cursor_val, cursor_id)
             
        query = self._apply_sorting(query, sort_col, params.sort_order)

        result = await self.session.execute(query.limit(params.limit + 1))
        return list(result.scalars().all())

    def _apply_filters(self, query: Select, params: BookQueryParams) -> Select:
        if params.status:
            query = query.where(Book.status == params.status)
        if params.author:
            query = query.where(Book.author == params.author)
        return query

    def _get_sort_column(self, sort_by: Optional[str]):
        if sort_by == "title":
            return Book.title
        if sort_by == "year_published":
            return Book.year_published
        return None

    def _apply_cursor(self, query: Select, sort_col, sort_order: str, cursor_val, cursor_id) -> Select:
        if sort_col is not None and cursor_val is not None:
            if sort_order == "desc":
                return query.where(or_(sort_col < cursor_val, and_(sort_col == cursor_val, Book.id < cursor_id)))
            else:
                return query.where(or_(sort_col > cursor_val, and_(sort_col == cursor_val, Book.id > cursor_id)))
        # Fallback ID cursor
        return query.where(Book.id > cursor_id)

    def _apply_sorting(self, query: Select, sort_col, sort_order: str) -> Select:
        if sort_col is not None:
            if sort_order == "desc":
                return query.order_by(desc(sort_col), desc(Book.id))
            return query.order_by(asc(sort_col), asc(Book.id))
        return query.order_by(asc(Book.id))

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
