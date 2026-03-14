import os

# Must be set BEFORE importing app modules so models.py picks up the override
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DB_ECHO"] = "false"

import pytest
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Monkey-patch app.models to use in-memory SQLite before loading app.main
import app.models as _models

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
_SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
_models.engine = _engine
_models.SessionLocal = _SessionLocal

from app.main import app
from app.models import Base, Book


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture(autouse=True)
def reset_db_data():
    session = _SessionLocal()
    try:
        session.query(Book).delete()
        session.commit()

        book = Book(
            title="1984",
            author="George Orwell",
            description="A dystopian novel",
            status="available",
            year_published=1949,
        )
        session.add(book)
        session.commit()
    finally:
        session.close()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_get_books(client):
    response = client.get("/api/books")
    assert response.status_code == 200
    data = response.get_json()["items"]
    assert len(data) == 1
    assert data[0]["title"] == "1984"


def test_get_book(client):
    books_response = client.get("/api/books")
    book_id = books_response.get_json()["items"][0]["id"]

    response = client.get(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert response.get_json()["title"] == "1984"


def test_get_book_not_found(client):
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/books/{random_id}")
    assert response.status_code == 404
    assert response.get_json()["message"] == "Book not found"


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
    data = response.get_json()
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
    book_id = books_response.get_json()["items"][0]["id"]

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
    assert response.get_json()["message"] == "Book not found"


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
    data1 = response1.get_json()
    assert len(data1["items"]) == 1
    assert data1["items"][0]["title"] == "1984"
    assert data1["total"] == 2
    assert data1["next_page"] is not None

    # Second page: limit 1, offset 1
    response2 = client.get("/api/books?limit=1&offset=1")
    assert response2.status_code == 200
    data2 = response2.get_json()
    assert len(data2["items"]) == 1
    assert data2["items"][0]["title"] == "Brave New World"
    assert data2["prev_page"] is not None


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
    data = response.get_json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "borrowed"

    response_avail = client.get("/api/books?status=available")
    assert response_avail.status_code == 200
    assert len(response_avail.get_json()["items"]) == 1


def test_get_books_filter_by_author(client):
    response = client.get("/api/books?author=George+Orwell")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["items"]) == 1
    assert data["items"][0]["author"] == "George Orwell"

    response_empty = client.get("/api/books?author=Unknown")
    assert response_empty.status_code == 200
    assert len(response_empty.get_json()["items"]) == 0


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
    data = response.get_json()
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "1984"
    assert data["items"][1]["title"] == "Animal Farm"


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
    data = response.get_json()
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Animal Farm"
    assert data["items"][1]["title"] == "1984"


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
    data = response.get_json()
    assert len(data["items"]) == 2
    assert data["items"][0]["year_published"] == 1949
    assert data["items"][1]["year_published"] == 1945
