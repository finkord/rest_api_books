from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database.session import get_db
from app.core.security import verify_token_type

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)):
    from app.auth.repository import UserRepository
    
    user_id = verify_token_type(token, "access")
    
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_auth_service(db: AsyncSession = Depends(get_db)):
    from app.auth.repository import UserRepository
    from app.auth.service import AuthService
    return AuthService(repository=UserRepository(db))

async def get_book_service(db: AsyncSession = Depends(get_db)):
    from app.books.repository import BookRepository
    from app.books.service import BookService
    return BookService(repository=BookRepository(db))
