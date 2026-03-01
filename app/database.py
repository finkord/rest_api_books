import os
from motor.motor_asyncio import AsyncIOMotorClient

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://admin:admin@mongo:27017/?authSource=admin")
DATABASE_NAME = os.getenv("MONGO_INITDB_DATABASE", "booksdb")

client = AsyncIOMotorClient(DATABASE_URL, uuidRepresentation="standard")

async def get_db():
    yield client[DATABASE_NAME]
