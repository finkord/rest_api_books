import uuid
from typing import List
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models import Book, User, RefreshSession
from app.schemas import BookRequest, UserCreate, RefreshTokenRequest
from app.repository import Repository, UserRepository, RefreshSessionRepository
from app.exceptions import NotFoundError, InvalidTokenError, ExpiredTokenError
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token_type,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from datetime import datetime, timezone, timedelta


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
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset
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
    def __init__(self, repository: UserRepository, session_repository: RefreshSessionRepository):
        self.repository = repository
        self.session_repository = session_repository

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
        
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        await self.session_repository.create(RefreshSession(
            refresh_token=refresh_token,
            user_id=user.id,
            expires_at=expires_at
        ))
        
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def refresh_token(self, request: RefreshTokenRequest) -> dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        db_session = await self.session_repository.get_by_token(request.refresh_token)
        if not db_session:
            raise credentials_exception
            
        is_expired = False
        try:
            payload = verify_token_type(request.refresh_token, "refresh")
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise credentials_exception
        except ExpiredTokenError:
            is_expired = True
        except (InvalidTokenError, ValueError):
            raise credentials_exception
            
        if is_expired:
            await self.session_repository.delete_by_token(request.refresh_token)
            raise HTTPException(status_code=401, detail="Refresh token expired")
            
        user = await self.repository.get_by_id(user_id=uuid.UUID(user_id_str))
        if user is None:
            raise credentials_exception
            
        await self.session_repository.delete_by_token(request.refresh_token)
            
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        await self.session_repository.create(RefreshSession(
            refresh_token=new_refresh_token,
            user_id=user.id,
            expires_at=expires_at
        ))
        
        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

    async def logout(self, request: RefreshTokenRequest) -> dict:
        deleted = await self.session_repository.delete_by_token(request.refresh_token)
        if not deleted:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        return {"message": "Logged out successfully"}
