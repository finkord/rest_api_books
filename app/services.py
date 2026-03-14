import uuid
import urllib.parse
from typing import List
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models import Book, User
from app.schemas import BookRequest, UserCreate, RefreshTokenRequest
from app.repository import Repository, UserRepository
from app.exceptions import NotFoundError, InvalidTokenError, ExpiredTokenError
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token_type,
)


class BookService:
    def __init__(self, repository: Repository):
        self.repository = repository

    async def get_books(
        self,
        status: str | None = None,
        author: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0
    ) -> dict:
        items, total = await self.repository.get_all(
            status=status,
            author=author,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        # Build base URL to append query parameters easily
        base_url = "/api/books"
        
        base_params = {}
        if status: base_params["status"] = status
        if author: base_params["author"] = author
        if sort_by: base_params["sort_by"] = sort_by
        base_params["sort_order"] = sort_order
        
        next_page = None
        if offset + limit < total:
            next_params = {**base_params, "limit": limit, "offset": offset + limit}
            next_page = f"{base_url}?{urllib.parse.urlencode(next_params)}"

        prev_page = None
        if offset > 0:
            prev_offset = max(0, offset - limit)
            prev_params = {**base_params, "limit": limit, "offset": prev_offset}
            prev_page = f"{base_url}?{urllib.parse.urlencode(prev_params)}"
            
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "next_page": next_page,
            "prev_page": prev_page
        }

    async def get_book(self, book_id: uuid.UUID) -> Book:
        book = await self.repository.get_by_id(book_id)
        if not book:
            raise NotFoundError("Book not found")
        return book

    async def create_book(self, book_request: BookRequest) -> Book:
        book = Book(
            title=book_request.title,
            author=book_request.author,
            description=book_request.description,
            status=book_request.status,
            year_published=book_request.year_published,
        )
        return await self.repository.create(book)

    async def delete_book(self, book_id: uuid.UUID) -> dict:
        deleted = await self.repository.delete(book_id)
        if not deleted:
            raise NotFoundError("Book not found")
        return {"message": "Book deleted"}


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register(self, user: UserCreate) -> User:
        existing_user = await self.repository.get_by_username(user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        hashed_password = await get_password_hash(user.password)
        db_user = User(username=user.username, hashed_password=hashed_password)
        return await self.repository.create(db_user)

    async def login(self, form_data: OAuth2PasswordRequestForm) -> dict:
        user = await self.repository.get_by_username(form_data.username)
        if not user or not await verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user.username})
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def refresh_token(self, request: RefreshTokenRequest) -> dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = verify_token_type(request.refresh_token, "refresh")
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except ExpiredTokenError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except InvalidTokenError:
            raise credentials_exception
            
        user = await self.repository.get_by_username(username=username)
        if user is None:
            raise credentials_exception
            
        access_token = create_access_token(data={"sub": user.username})
        new_refresh_token = create_refresh_token(data={"sub": user.username})
        
        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
