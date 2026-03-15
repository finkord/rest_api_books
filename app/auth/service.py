import uuid
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timezone, timedelta

from app.auth.models import User, RefreshSession
from app.auth.schemas import UserCreate, RefreshTokenRequest, Token, MessageResponse
from app.auth.repository import UserRepository, RefreshSessionRepository
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
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        await self.session_repository.create(RefreshSession(
            refresh_token=refresh_token,
            user_id=user.id,
            expires_at=expires_at
        ))
        
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def refresh_token(self, request: RefreshTokenRequest) -> Token:
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
        
        return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")

    async def logout(self, request: RefreshTokenRequest) -> MessageResponse:
        deleted = await self.session_repository.delete_by_token(request.refresh_token)
        if not deleted:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        return MessageResponse(message="Logged out successfully")
