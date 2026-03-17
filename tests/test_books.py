import pytest
import uuid

pytestmark = pytest.mark.asyncio

async def test_get_books(auth_client):
    response = await auth_client.get("/api/books")
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["title"] == "1984"

async def test_get_book(auth_client):
    books_response = await auth_client.get("/api/books")
    book_id = books_response.json()["items"][0]["id"]

    response = await auth_client.get(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "1984"

async def test_get_book_not_found(auth_client):
    random_id = str(uuid.uuid4())
    response = await auth_client.get(f"/api/books/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

async def test_create_book(auth_client):
    new_book = {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1932,
    }
    response = await auth_client.post("/api/books", json=[new_book])
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "id" in data[0]
    assert data[0]["title"] == new_book["title"]

async def test_create_book_invalid_title(auth_client):
    new_book = {
        "title": "_Invalid",
        "author": "Author",
        "description": "Desc with length",
        "status": "available",
        "year_published": 2000,
    }
    response = await auth_client.post("/api/books", json=[new_book])
    assert response.status_code == 422

async def test_delete_book(auth_client):
    books_response = await auth_client.get("/api/books")
    book_id = books_response.json()["items"][0]["id"]

    response = await auth_client.delete(f"/api/books/{book_id}")
    assert response.status_code == 200

    response = await auth_client.get(f"/api/books/{book_id}")
    assert response.status_code == 404

async def test_create_book_empty_fields(auth_client):
    new_book = {
        "title": "   ",
        "author": "Author",
        "description": "Valid description",
        "status": "available",
        "year_published": 2000,
    }
    response = await auth_client.post("/api/books", json=[new_book])
    assert response.status_code == 422

async def test_create_book_invalid_status(auth_client):
    new_book = {
        "title": "Valid Title",
        "author": "Author",
        "description": "Valid description",
        "status": "lost",
        "year_published": 2000,
    }
    response = await auth_client.post("/api/books", json=[new_book])
    assert response.status_code == 422

async def test_create_book_future_year(auth_client):
    new_book = {
        "title": "Future Book",
        "author": "Author",
        "description": "Valid description",
        "status": "available",
        "year_published": 2050,
    }
    response = await auth_client.post("/api/books", json=[new_book])
    assert response.status_code == 422

async def test_delete_book_not_found(auth_client):
    random_id = str(uuid.uuid4())
    response = await auth_client.delete(f"/api/books/{random_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

async def test_get_books_pagination(auth_client):
    new_book = {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1932,
    }
    await auth_client.post("/api/books", json=[new_book])

    response1 = await auth_client.get("/api/books?limit=1&offset=0&sort_by=title&sort_order=asc")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["items"]) == 1
    assert data1["items"][0]["title"] == "1984" 
    assert data1["total"] == 2
    assert data1["next_page"] is not None

    response2 = await auth_client.get("/api/books?limit=1&offset=1&sort_by=title&sort_order=asc")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["items"]) == 1
    assert data2["items"][0]["title"] == "Brave New World"
    assert data2["prev_page"] is not None

async def test_get_books_filter_by_status(auth_client):
    new_book = {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "description": "Another dystopian novel",
        "status": "borrowed",
        "year_published": 1932,
    }
    await auth_client.post("/api/books", json=[new_book])

    response = await auth_client.get("/api/books?status=borrowed")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "borrowed"
    
    response_avail = await auth_client.get("/api/books?status=available")
    assert response_avail.status_code == 200
    assert len(response_avail.json()["items"]) == 1

async def test_get_books_filter_by_author(auth_client):
    response = await auth_client.get("/api/books?author=George+Orwell")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["author"] == "George Orwell"

    response_empty = await auth_client.get("/api/books?author=Unknown")
    assert response_empty.status_code == 200
    assert len(response_empty.json()["items"]) == 0

async def test_get_books_sort_by_title_asc(auth_client):
    new_book = {
        "title": "Animal Farm",
        "author": "George Orwell",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1945,
    }
    await auth_client.post("/api/books", json=[new_book])

    response = await auth_client.get("/api/books?sort_by=title&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "1984" 
    assert data["items"][1]["title"] == "Animal Farm"

async def test_get_books_sort_by_title_desc(auth_client):
    new_book = {
        "title": "Animal Farm",
        "author": "George Orwell",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1945,
    }
    await auth_client.post("/api/books", json=[new_book])

    response = await auth_client.get("/api/books?sort_by=title&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Animal Farm"
    assert data["items"][1]["title"] == "1984"

async def test_get_books_sort_by_year_published(auth_client):
    new_book = {
        "title": "Animal Farm",
        "author": "George Orwell",
        "description": "Another dystopian novel",
        "status": "available",
        "year_published": 1945,
    }
    await auth_client.post("/api/books", json=[new_book])

    response = await auth_client.get("/api/books?sort_by=year_published&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["year_published"] == 1949 
    assert data["items"][1]["year_published"] == 1945
