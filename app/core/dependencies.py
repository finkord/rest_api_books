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

from fastapi import Request
from app.core.rate_limiter import RedisRateLimiter

# Initialize a global limiter instance
rate_limiter = RedisRateLimiter()

async def rate_limit(request: Request, user_id: str | None = None):
    # Requirement: If token is provided but invalid, return 401 instead of falling back to IP limit.
    if user_id is None:
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            raw_token = token.split(" ")[1]
            try:
                user_id_uuid = verify_token_type(raw_token, "access")
                user_id = str(user_id_uuid)
            except HTTPException as e:
                raise e

    if user_id:
        key = f"ratelimit:user:{user_id}"
        limit = 10
    else:
        # Check for proxy headers first to get the real client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            host = forwarded_for.split(",")[0].strip()
        else:
            real_ip = request.headers.get("X-Real-IP")
            host = real_ip if real_ip else (request.client.host if request.client else "unknown")
        key = f"ratelimit:ip:{host}"
        limit = 2

    allowed = await rate_limiter.check_allowance(key=key, limit=limit, window=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too Many Requests"
        )

class RateLimitDependency:
    async def __call__(self, request: Request):
        token = request.headers.get("Authorization")
        user_id = None
        
        if token and token.startswith("Bearer "):
            raw_token = token.split(" ")[1]
            try:
                user_id_uuid = verify_token_type(raw_token, "access")
                user_id = str(user_id_uuid)
            except HTTPException as e:
                # Re-raise the exception to deny access strictly rather than falling back to IP limits
                raise e

        await rate_limit(request, user_id)
