import os
import pytest
import uuid
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from app.main import app
from app.models import Base, engine, async_session, Book

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(init_db())
    yield
    async def cleanup_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(cleanup_db())

@pytest.fixture(autouse=True)
def reset_db_data():
    async def reset():
        async with async_session() as session:
            await session.execute(text("DELETE FROM books"))
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
    asyncio.run(reset())

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_books(client):
    response = client.get("/api/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "1984"

def test_get_book(client):
    books_response = client.get("/api/books")
    book_id = books_response.json()[0]["id"]

    response = client.get(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "1984"

def test_get_book_not_found(client):
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/books/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

def test_create_book(client):
    new_book = {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1932,
    }
    response = client.post("/api/books", json=new_book)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == new_book["title"]

def test_create_book_invalid_title(client):
    new_book = {
        "title": "_Invalid",
        "author": "Author",
        "description": "Desc with length",
        "status": "available",
        "year_published": 2000,
    }
    response = client.post("/api/books", json=new_book)
    assert response.status_code == 422

def test_delete_book(client):
    books_response = client.get("/api/books")
    book_id = books_response.json()[0]["id"]

    response = client.delete(f"/api/books/{book_id}")
    assert response.status_code == 200

    response = client.get(f"/api/books/{book_id}")
    assert response.status_code == 404
