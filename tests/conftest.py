import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from app.main import app
from app.database.session import Base, engine, async_session
from app.database.redis import get_redis
from unittest.mock import AsyncMock, MagicMock
from app.books.models import Book
from sqlalchemy import text

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(autouse=True)
async def mock_redis():
    mock = AsyncMock()
    mock.exists.return_value = 0
    mock.setex = AsyncMock()
    
    # Mock for Pipeline
    class MockPipeline:
        def __init__(self):
            # Default results for sliding window: [zremrange, zadd, zcard, pexpire]
            self.results = [None, None, 1, None] 
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        def zremrangebyscore(self, *args, **kwargs): return self
        def zadd(self, *args, **kwargs): return self
        def zcard(self, *args, **kwargs): return self
        def pexpire(self, *args, **kwargs): return self
        async def execute(self): return self.results
        def set_count(self, val):
            self.results[2] = val

    mock.pipeline_instance = MockPipeline()
    mock.pipeline = MagicMock(return_value=mock.pipeline_instance)
    mock.zrem = AsyncMock()
    
    return mock

@pytest_asyncio.fixture(autouse=True)
async def setup_redis_override(mock_redis, mocker):
    mocker.patch("redis.asyncio.from_url", return_value=mock_redis)
    from app.database.redis import get_redis as actual_get_redis
    app.dependency_overrides[actual_get_redis] = lambda: mock_redis
    yield
    app.dependency_overrides.pop(actual_get_redis, None)

@pytest_asyncio.fixture(autouse=True)
async def reset_db_data():
    async with async_session() as session:
        await session.execute(text("DELETE FROM books"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()

        book = Book(
            title="1984",
            author="George Orwell",
            description="A dystopian novel",
            status="available",
            year_published=1949,
        )
        session.add(book)
        await session.commit()

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest_asyncio.fixture
async def auth_client_and_tokens(client):
    # Register a dev user
    user_data = {"username": "testuser", "password": "testpassword"}
    await client.post("/api/auth/register", json=user_data)
    
    # Login to get token
    login_data = {"username": "testuser", "password": "testpassword"}
    token_response = await client.post("/api/auth/login", data=login_data)
    tokens = token_response.json()
    
    # Create an authenticated client
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as c:
        yield c, tokens

@pytest_asyncio.fixture
async def auth_client(auth_client_and_tokens):
    client, _ = auth_client_and_tokens
    return client
