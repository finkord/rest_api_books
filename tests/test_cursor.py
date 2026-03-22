import os
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import pytest_asyncio

# Force test database URL BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_cursor.db"

from app.main import app
from app.models import Base, engine, async_session, Book
from app.schemas import BookStatus

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Initializes the test database and handles cleanup after the session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provides a clean database session for each test."""
    async with async_session() as session:
        yield session
        # Cleanup data after each test to ensure isolation
        await session.execute(text("DELETE FROM books"))
        await session.commit()

@pytest_asyncio.fixture(scope="function")
async def client():
    """Provides an async test client for the FastAPI application."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

async def create_books(session: AsyncSession, books_data: list):
    """Utility to batch create books for testing."""
    books = [Book(**data) for data in books_data]
    session.add_all(books)
    await session.commit()
    # Refreshing all is slow, but we mostly just need them in DB
    return books

@pytest.mark.asyncio
async def test_pagination_by_id_default(client, db_session):
    """Verifies default pagination by ID (ASC) works across multiple pages."""
    books_data = [
        {"title": f"Book {i}", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2000 + i}
        for i in range(5)
    ]
    created_books = await create_books(db_session, books_data)
    # Default sorting is ID ASC
    created_books.sort(key=lambda x: x.id)

    # Page 1: limit 2
    response = await client.get("/api/books?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == str(created_books[0].id)
    assert data["items"][1]["id"] == str(created_books[1].id)
    assert data["next_cursor"] is not None

    # Page 2: limit 2
    cursor = data["next_cursor"]
    response = await client.get(f"/api/books?limit=2&cursor={cursor}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == str(created_books[2].id)
    assert data["items"][1]["id"] == str(created_books[3].id)
    assert data["next_cursor"] is not None

    # Page 3: final page
    cursor = data["next_cursor"]
    response = await client.get(f"/api/books?limit=2&cursor={cursor}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(created_books[4].id)
    assert data["next_cursor"] is None

@pytest.mark.asyncio
async def test_pagination_by_title_asc(client, db_session):
    """Tests pagination sorted by title ASC, including tie-breaking with ID."""
    books_data = [
        {"title": "B", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2000},
        {"title": "A", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2001},
        {"title": "B", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2002},
    ]
    created = await create_books(db_session, books_data)
    
    # Expected order: A, B (smaller ID), B (larger ID)
    b_books = [b for b in created if b.title == "B"]
    b_books.sort(key=lambda x: x.id)
    a_book = [b for b in created if b.title == "A"][0]
    expected_ids = [str(a_book.id), str(b_books[0].id), str(b_books[1].id)]

    response = await client.get("/api/books?limit=2&sort_by=title&sort_order=asc")
    data = response.json()
    assert [i["id"] for i in data["items"]] == expected_ids[:2]
    
    cursor = data["next_cursor"]
    response = await client.get(f"/api/books?limit=2&sort_by=title&sort_order=asc&cursor={cursor}")
    data = response.json()
    assert [i["id"] for i in data["items"]] == expected_ids[2:]
    assert data["next_cursor"] is None

@pytest.mark.asyncio
async def test_pagination_by_title_desc(client, db_session):
    """Tests pagination sorted by title DESC, including tie-breaking with ID (DESC)."""
    books_data = [
        {"title": "A", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2000},
        {"title": "B", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2001},
        {"title": "B", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2002},
    ]
    created = await create_books(db_session, books_data)
    
    # Expected: B (larger ID), B (smaller ID), A
    b_books = [b for b in created if b.title == "B"]
    b_books.sort(key=lambda x: x.id, reverse=True)
    a_book = [b for b in created if b.title == "A"][0]
    expected_ids = [str(b_books[0].id), str(b_books[1].id), str(a_book.id)]

    response = await client.get("/api/books?limit=2&sort_by=title&sort_order=desc")
    data = response.json()
    assert [i["id"] for i in data["items"]] == expected_ids[:2]
    
    cursor = data["next_cursor"]
    response = await client.get(f"/api/books?limit=2&sort_by=title&sort_order=desc&cursor={cursor}")
    data = response.json()
    assert [i["id"] for i in data["items"]] == expected_ids[2:]

@pytest.mark.asyncio
async def test_pagination_by_year_desc(client, db_session):
    """Tests pagination sorted by year DESC."""
    books_data = [
        {"title": "T1", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2010},
        {"title": "T2", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2020},
        {"title": "T3", "author": "A", "description": "D", "status": BookStatus.available, "year_published": 2020},
    ]
    created = await create_books(db_session, books_data)
    y2020 = [b for b in created if b.year_published == 2020]
    y2020.sort(key=lambda x: x.id, reverse=True)
    y2010 = [b for b in created if b.year_published == 2010][0]
    expected_ids = [str(y2020[0].id), str(y2020[1].id), str(y2010.id)]

    response = await client.get("/api/books?limit=2&sort_by=year_published&sort_order=desc")
    data = response.json()
    assert [i["id"] for i in data["items"]] == expected_ids[:2]
    
    cursor = data["next_cursor"]
    response = await client.get(f"/api/books?limit=2&sort_by=year_published&sort_order=desc&cursor={cursor}")
    data = response.json()
    assert [i["id"] for i in data["items"]] == expected_ids[2:]

@pytest.mark.asyncio
async def test_filtering_and_pagination(client, db_session):
    """Verifies that filtering parameters are respected alongside cursor pagination."""
    books_data = [
        {"title": f"B{i}", "author": "George", "description": "D", "status": BookStatus.available, "year_published": 2000} for i in range(3)
    ] + [
        {"title": f"X{i}", "author": "Other", "description": "D", "status": BookStatus.borrowed, "year_published": 2000} for i in range(2)
    ]
    await create_books(db_session, books_data)
    
    # Filter by author "George", limit 2
    response = await client.get("/api/books?author=George&limit=2")
    data = response.json()
    assert len(data["items"]) == 2
    assert all(i["author"] == "George" for i in data["items"])
    assert data["next_cursor"] is not None
    
    cursor = data["next_cursor"]
    response = await client.get(f"/api/books?author=George&limit=2&cursor={cursor}")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["author"] == "George"
    assert data["next_cursor"] is None

@pytest.mark.asyncio
async def test_invalid_cursor(client):
    """Ensures a 400 error is returned for malformed cursor values."""
    response = await client.get("/api/books?cursor=invalid_base64_or_json")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid cursor format"

@pytest.mark.asyncio
async def test_empty_results(client, db_session):
    """Verifies behavior when no records match the query."""
    response = await client.get("/api/books")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["next_cursor"] is None
