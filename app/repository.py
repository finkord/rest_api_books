from typing import List, Optional
from pydantic_mongo import AsyncAbstractRepository
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models import Book

class Repository(AsyncAbstractRepository[Book]):
    class Meta:
        collection_name = "books"

    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database)

    async def get_all(self, limit: int = 10, offset: int = 0) -> List[Book]:
        cursor = self.get_collection().find({}).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.to_model(doc) for doc in docs]

    async def get_by_id(self, book_id: str) -> Optional[Book]:
        return await self.find_one_by_id(book_id)

    async def create(self, book: Book) -> Book:
        await self.save(book)
        return book

    async def delete(self, book_id: str) -> bool:
        result = await self.get_collection().delete_one({"_id": book_id})
        return result.deleted_count > 0
