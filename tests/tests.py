import pytest
import uuid
import asyncio
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.models import Book
from app.database import get_db

mock_client = AsyncMongoMockClient(uuidRepresentation="standard")
mock_db = mock_client["test_booksdb"]

async def override_get_db():
    yield mock_db

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def reset_db_data():
    async def reset():
        await mock_db.books.delete_many({})

        book = Book(
            title="1984",
            author="George Orwell",
            description="A dystopian novel",
            status="available",
            year_published=1949,
        )
        
        from app.repository import Repository
        repo = Repository(mock_db)
        await repo.create(book)

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
    new_book = {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1932,
    }
    client.post("/api/books", json=new_book)
    
    response1 = client.get("/api/books?limit=1&offset=0")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 1
    assert data1[0]["title"] == "1984"

    response2 = client.get("/api/books?limit=1&offset=1")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 1
    assert data2[0]["title"] == "Brave New World"
