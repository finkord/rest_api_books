import uuid
import urllib.parse
from typing import List, Literal
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import async_session, User
from app.schemas import BookRequest, BookResponse, PaginatedBookResponse
from app.dependencies import get_db
from app.services import BookService
from app.repository import Repository
from app.security import get_current_user

router = APIRouter(prefix="/api", tags=["Books"])


async def get_service(db: AsyncSession = Depends(get_db)):
    return BookService(repository=Repository(db))


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/books", response_model=PaginatedBookResponse)
async def get_books(
    request: Request,
    status: Literal["available", "borrowed"] | None = Query(None, description="Filter by status"),
    author: str | None = Query(None, description="Filter by author"),
    sort_by: Literal["title", "year_published"] | None = Query(None, description="Sort by 'title' or 'year_published'"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort order: 'asc' or 'desc'"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: BookService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    result = await service.get_books(
        status=status,
        author=author,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    
    total = result.total
    
    base_url = str(request.url.replace(query=""))
    query_params = dict(request.query_params)
    
    next_page = None
    if offset + limit < total:
        next_params = {**query_params, "limit": limit, "offset": offset + limit}
        next_page = f"{base_url}?{urllib.parse.urlencode(next_params)}"

    prev_page = None
    if offset > 0:
        prev_offset = max(0, offset - limit)
        prev_params = {**query_params, "limit": limit, "offset": prev_offset}
        prev_page = f"{base_url}?{urllib.parse.urlencode(prev_params)}"
        
    return PaginatedBookResponse(
        items=result.items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        next_page=next_page,
        prev_page=prev_page
    )


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: uuid.UUID, service: BookService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return await service.get_book(book_id)


@router.post("/books", status_code=201, response_model=BookResponse)
async def create_book(book: BookRequest, service: BookService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return await service.create_book(book)


@router.delete("/books/{book_id}")
async def delete_book(book_id: uuid.UUID, service: BookService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return await service.delete_book(book_id)
