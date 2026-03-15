from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import uuid

from app.core.database import async_session
from app.exceptions import ExpiredTokenError, InvalidTokenError
from app.core.security import verify_token_type

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_db():
    async with async_session() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)):
    from app.auth.repository import UserRepository
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token_type(token, "access")
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except ExpiredTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except (InvalidTokenError, ValueError):
        raise credentials_exception
    
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_auth_service(db: AsyncSession = Depends(get_db)):
    from app.auth.repository import UserRepository, RefreshSessionRepository
    from app.auth.service import AuthService
    return AuthService(
        repository=UserRepository(db),
        session_repository=RefreshSessionRepository(db)
    )

async def get_book_service(db: AsyncSession = Depends(get_db)):
    from app.books.repository import BookRepository
    from app.books.service import BookService
    return BookService(repository=BookRepository(db))
