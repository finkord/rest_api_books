import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import db, Book
import uuid

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    db.clear()
    book = Book(
        title="1984",
        author="George Orwell",
        description="A dystopian novel",
        status="available",
        year_published=1949,
    )
    db.append(book)
    yield
    db.clear()


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_books():
    response = client.get("/api/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "1984"


def test_get_book():
    books_response = client.get("/api/books")
    book_id = books_response.json()[0]["id"]

    response = client.get(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "1984"


def test_get_book_not_found():
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/books/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_create_book():
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


def test_create_book_invalid_title():
    new_book = {
        "title": "_Invalid",
        "author": "Author",
        "description": "Desc with length",
        "status": "available",
        "year_published": 2000,
    }
    response = client.post("/api/books", json=new_book)
    assert response.status_code == 422


def test_delete_book():
    books_response = client.get("/api/books")
    book_id = books_response.json()[0]["id"]

    response = client.delete(f"/api/books/{book_id}")
    assert response.status_code == 200

    response = client.get(f"/api/books/{book_id}")
    assert response.status_code == 404
