from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from app.database.session import get_db
from app.database.redis import get_redis
from app.core.security import verify_token_type, SECRET_KEY, ALGORITHM
from app.core.rate_limiter import RedisRateLimiter
import jwt
from redis.asyncio import Redis
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
limiter = RedisRateLimiter()

async def rate_limit(request: Request, redis: Redis = Depends(get_redis)):
    # Try to get user_id from token without raising exception if missing/invalid
    user_id = None
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        try:
            raw_token = token.split(" ")[1]
            payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
        except jwt.PyJWTError:
            pass
            
    if user_id:
        key = f"ratelimit:user:{user_id}"
        limit = settings.RATE_LIMIT_AUTH_USER
    else:
        # Get IP (simplified, following user's original archived logic)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            host = forwarded_for.split(",")[0].strip()
        else:
            host = request.client.host if request.client else "unknown"
        key = f"ratelimit:ip:{host}"
        limit = settings.RATE_LIMIT_GUEST_USER
        
    allowed = await limiter.check_allowance(key, limit, redis_client=redis)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too Many Requests"
        )

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    from app.auth.repository import UserRepository
    
    user_id = await verify_token_type(token, "access", redis_client=redis)
    
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_auth_service(db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    from app.auth.repository import UserRepository
    from app.auth.service import AuthService
    return AuthService(repository=UserRepository(db), redis=redis)

async def get_book_service(db: AsyncSession = Depends(get_db)):
    from app.books.repository import BookRepository
    from app.books.service import BookService
    return BookService(repository=BookRepository(db))
