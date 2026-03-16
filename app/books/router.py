import uuid
from typing import Literal, List
from fastapi import APIRouter, Depends, Query, Request

from app.auth.models import User
from app.books.schemas import BookRequest, BookResponse, PaginatedBookResponse
from app.core.dependencies import (
    get_book_service,
    get_current_user,
    rate_limit
)
from app.core.utils import generate_pagination_links
from app.books.service import BookService

router = APIRouter(
    prefix="/api/books",
    tags=["Books"],
    dependencies=[Depends(rate_limit), Depends(get_current_user)]
)

@router.get("", response_model=PaginatedBookResponse)
async def get_books(
    request: Request,
    status: Literal["available", "borrowed"] | None = Query(None, description="Filter by status"),
    author: str | None = Query(None, description="Filter by author"),
    sort_by: Literal["title", "year_published"] | None = Query(None, description="Sort by 'title' or 'year_published'"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort order: 'asc' or 'desc'"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: BookService = Depends(get_book_service),
):
    result = await service.get_books(
        status=status,
        author=author,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    
    pagination_links = generate_pagination_links(
        request=request, 
        total=result.total, 
        limit=result.limit, 
        offset=result.offset
    )
        
    return PaginatedBookResponse(
        items=result.items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        next_page=pagination_links["next_page"],
        prev_page=pagination_links["prev_page"]
    )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: uuid.UUID,
    service: BookService = Depends(get_book_service)
):
    return await service.get_book(book_id)


# @router.post("", status_code=201, response_model=BookResponse)
# async def create_book(
#     book: BookRequest,
#     service: BookService = Depends(get_book_service)
# ):
#     return await service.create_book(book)

@router.post("", status_code=201, response_model=List[BookResponse])
async def create_books(
    books: List[BookRequest], 
    service: BookService = Depends(get_book_service)
):
    return await service.create_books(books)

@router.delete("/{book_id}")
async def delete_book(
    book_id: uuid.UUID,
    service: BookService = Depends(get_book_service)
):
    return await service.delete_book(book_id)
