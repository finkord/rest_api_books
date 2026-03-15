import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from app.core.database import Base

class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(400), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    year_published: Mapped[int] = mapped_column(Integer, nullable=False)
