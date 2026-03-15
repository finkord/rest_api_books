import uuid
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timezone, timedelta

from app.auth.models import User
from app.auth.schemas import UserCreate, RefreshTokenRequest, Token, MessageResponse
from app.auth.repository import UserRepository
from app.exceptions import InvalidTokenError, ExpiredTokenError
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token_type,
    REFRESH_TOKEN_EXPIRE_DAYS
)


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

    async def login(self, form_data: OAuth2PasswordRequestForm) -> Token:
        user = await self.repository.get_by_username(form_data.username)
        if not user or not await verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def refresh_token(self, request: RefreshTokenRequest) -> Token:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = verify_token_type(request.refresh_token, "refresh")
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise credentials_exception
        except ExpiredTokenError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except (InvalidTokenError, ValueError):
            raise credentials_exception
            
        user = await self.repository.get_by_id(user_id=uuid.UUID(user_id_str))
        if user is None:
            raise credentials_exception
            
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")

    async def logout(self, request: RefreshTokenRequest) -> MessageResponse:
        # With stateless JWTs, server-side logout is a no-op unless we implement a blacklist.
        # The client should simply discard the token.
        return MessageResponse(message="Logged out successfully")
