import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.auth.models import User
from app.core.security import get_password_hash

# Use the provided PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:admin@postgres:5432/booksdb")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def seed_users():
    # Create test users with hashed passwords
    users = [
        User(
            username="admin",
            hashed_password=get_password_hash("books-admin")
        ),
        User(
            username="finkord",
            hashed_password=get_password_hash("finkord")
        )
    ]
    
    async with async_session() as session:
        session.add_all(users)
        await session.commit()
        print("Users seeded successfully.")
        
if __name__ == "__main__":
    asyncio.run(seed_users())