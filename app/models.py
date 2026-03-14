from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.mongodb_db_name]

# Expose books collection
books_collection = db.books
