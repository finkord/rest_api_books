import jwt
from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.models import User
from app.auth.schemas import UserCreate, RefreshTokenRequest, Token
from app.auth.repository import UserRepository
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_refresh_token,
    verify_token_type,
    blacklist_token,
    SECRET_KEY,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from redis.asyncio import Redis


class AuthService:
    def __init__(self, repository: UserRepository, redis: Redis):
        self.repository = repository
        self.redis = redis

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
        user_id = await verify_token_type(request.refresh_token, "refresh", redis_client=self.redis)
            
        user = await self.repository.get_by_id(user_id=user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Blacklist old refresh token
        try:
            payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            if jti:
                await blacklist_token(self.redis, jti, REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        except jwt.PyJWTError:
            pass
            
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")

    async def logout(self, access_token: str, refresh_token: Optional[str] = None):
        # Blacklist access token
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            if jti:
                await blacklist_token(self.redis, jti, ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        except jwt.PyJWTError:
            pass
            
        # Blacklist refresh token if provided
        if refresh_token:
            try:
                payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
                jti = payload.get("jti")
                if jti:
                    await blacklist_token(self.redis, jti, REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
            except jwt.PyJWTError:
                pass

