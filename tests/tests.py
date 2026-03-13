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


def test_create_book_empty_fields(client):
    new_book = {
        "title": "   ",
        "author": "Author",
        "description": "Valid description",
        "status": "available",
        "year_published": 2000,
    }
    response = client.post("/api/books", json=new_book)
    assert response.status_code == 422


def test_create_book_invalid_status(client):
    new_book = {
        "title": "Valid Title",
        "author": "Author",
        "description": "Valid description",
        "status": "lost",
        "year_published": 2000,
    }
    response = client.post("/api/books", json=new_book)
    assert response.status_code == 422


def test_create_book_future_year(client):
    new_book = {
        "title": "Future Book",
        "author": "Author",
        "description": "Valid description",
        "status": "available",
        "year_published": 2050,
    }
    response = client.post("/api/books", json=new_book)
    assert response.status_code == 422


def test_delete_book_not_found(client):
    random_id = str(uuid.uuid4())
    response = client.delete(f"/api/books/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_get_books_pagination(client):
    # Add an additional book
    new_book = {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1932,
    }
    client.post("/api/books", json=new_book)

    # First page: limit 1, offset 0
    response1 = client.get("/api/books?limit=1&offset=0")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 1
    assert data1[0]["title"] == "1984"  # According to reset fixture

    # Second page: limit 1, offset 1
    response2 = client.get("/api/books?limit=1&offset=1")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 1
    assert data2[0]["title"] == "Brave New World"


def test_get_books_filter_by_status(client):
    new_book = {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "description": "Another dystopian novel",
        "status": "borrowed",
        "year_published": 1932,
    }
    client.post("/api/books", json=new_book)

    response = client.get("/api/books?status=borrowed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "borrowed"
    
    response_avail = client.get("/api/books?status=available")
    assert response_avail.status_code == 200
    assert len(response_avail.json()) == 1


def test_get_books_filter_by_author(client):
    response = client.get("/api/books?author=George+Orwell")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["author"] == "George Orwell"

    response_empty = client.get("/api/books?author=Unknown")
    assert response_empty.status_code == 200
    assert len(response_empty.json()) == 0


def test_get_books_sort_by_title_asc(client):
    new_book = {
        "title": "Animal Farm",
        "author": "George Orwell",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1945,
    }
    client.post("/api/books", json=new_book)

    response = client.get("/api/books?sort_by=title&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "1984" # '1' comes before 'A' in ascii
    assert data[1]["title"] == "Animal Farm"


def test_get_books_sort_by_title_desc(client):
    new_book = {
        "title": "Animal Farm",
        "author": "George Orwell",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1945,
    }
    client.post("/api/books", json=new_book)

    response = client.get("/api/books?sort_by=title&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Animal Farm"
    assert data[1]["title"] == "1984"


def test_get_books_sort_by_year_published(client):
    new_book = {
        "title": "Animal Farm",
        "author": "George Orwell",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1945,
    }
    client.post("/api/books", json=new_book)

    response = client.get("/api/books?sort_by=year_published&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["year_published"] == 1949 # 1984 was published in 1949
    assert data[1]["year_published"] == 1945
