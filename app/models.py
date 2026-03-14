"""
Database models and SQLAlchemy engine configuration.
"""
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Enum

from app.config import settings
from app.schemas import BookStatus

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Book(Base):
    """
    SQLAlchemy model representing a Book entity in the database.
    """
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(400), nullable=False)
    status: Mapped[BookStatus] = mapped_column(Enum(BookStatus, native_enum=False), nullable=False)
    year_published: Mapped[int] = mapped_column(Integer, nullable=False)
