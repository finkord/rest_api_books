import pytest
import uuid
import pymongo
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.config import settings
from app.api import get_service
from app.services import BookService
from app.repository import Repository

# Override settings to use a test database
settings.mongodb_url = "mongodb://admin:adminpassword@localhost:27017/?authSource=admin"
settings.mongodb_db_name = "library_test"

# Create a sync client for fixture setup/teardown
# Ensure local tests can run without blocking the event loop
sync_client = pymongo.MongoClient(settings.mongodb_url)
sync_collection = sync_client[settings.mongodb_db_name]["books"]

# Create an async collection for dependency injection dynamically per request
async def override_get_service():
    test_client = AsyncIOMotorClient(settings.mongodb_url)
    test_collection = test_client[settings.mongodb_db_name]["books"]
    return BookService(repository=Repository(collection=test_collection))

app.dependency_overrides[get_service] = override_get_service

@pytest.fixture(autouse=True)
def reset_db_data():
    sync_collection.delete_many({})
    sync_collection.insert_one({
        "title": "1984",
        "author": "George Orwell",
        "description": "A dystopian novel",
        "status": "available",
        "year_published": 1949,
    })
    yield
    sync_collection.delete_many({})

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
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["title"] == "1984"

def test_get_book(client):
    books_response = client.get("/api/books")
    book_id = books_response.json()["items"][0]["id"]

    response = client.get(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "1984"

def test_get_book_not_found(client):
    random_id = "5f50c31e1c9d440000d1c000"
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
    response = client.post("/api/books", json=[new_book])
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 1
    assert "id" in data[0]
    assert data[0]["title"] == new_book["title"]

def test_create_book_invalid_title(client):
    new_book = {
        "title": "_Invalid",
        "author": "Author",
        "description": "Desc with length",
        "status": "available",
        "year_published": 2000,
    }
    response = client.post("/api/books", json=[new_book])
    assert response.status_code == 422

def test_delete_book(client):
    books_response = client.get("/api/books")
    book_id = books_response.json()["items"][0]["id"]

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
    response = client.post("/api/books", json=[new_book])
    assert response.status_code == 422

def test_create_book_invalid_status(client):
    new_book = {
        "title": "Valid Title",
        "author": "Author",
        "description": "Valid description",
        "status": "lost",
        "year_published": 2000,
    }
    response = client.post("/api/books", json=[new_book])
    assert response.status_code == 422

def test_create_book_future_year(client):
    new_book = {
        "title": "Future Book",
        "author": "Author",
        "description": "Valid description",
        "status": "available",
        "year_published": 2050,
    }
    response = client.post("/api/books", json=[new_book])
    assert response.status_code == 422

def test_delete_book_not_found(client):
    random_id = "5f50c31e1c9d440000d1c000"
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
    client.post("/api/books", json=[new_book])

    response1 = client.get("/api/books?limit=1&offset=0")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["items"]) == 1
    assert data1["items"][0]["title"] == "1984"
    assert data1["total"] == 2
    assert data1["next_page"] is not None

    response2 = client.get("/api/books?limit=1&offset=1")
    assert response2.status_code == 200
    data2 = response2.json()
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
    client.post("/api/books", json=[new_book])

    response = client.get("/api/books?status=borrowed")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "borrowed"
    
    response_avail = client.get("/api/books?status=available")
    assert response_avail.status_code == 200
    assert len(response_avail.json()["items"]) == 1

def test_get_books_filter_by_author(client):
    response = client.get("/api/books?author=George+Orwell")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["author"] == "George Orwell"

    response_empty = client.get("/api/books?author=Unknown")
    assert response_empty.status_code == 200
    assert len(response_empty.json()["items"]) == 0

def test_get_books_sort_by_title_asc(client):
    new_book = {
        "title": "Animal Farm",
        "author": "George Orwell",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1945,
    }
    client.post("/api/books", json=[new_book])

    response = client.get("/api/books?sort_by=title&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
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
    client.post("/api/books", json=[new_book])

    response = client.get("/api/books?sort_by=title&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
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
    client.post("/api/books", json=[new_book])

    response = client.get("/api/books?sort_by=year_published&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["year_published"] == 1949
    assert data["items"][1]["year_published"] == 1945
