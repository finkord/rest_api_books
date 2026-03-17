# Rate Limiter Archive

This file contains the rate limiting logic and related infrastructure code that was removed from the project.

## [app/core/rate_limiter.py](file:///home/finkord/dev/rest_api_cnu/app/core/rate_limiter.py)

```python
import time
import logging
from typing import Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    def __init__(self, redis_url: Optional[str] = None):
        if redis_url is None:
            from app.core.config import settings
            redis_url = settings.REDIS_URL
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

    async def check_allowance(self, key: str, limit: int, window: int = 60) -> bool:
        """
        Check if the request is allowed based on the sliding window rate limiting algorithm.
        Returns True if allowed (or fail-open on error), False if limit exceeded.
        """
        try:
            now_ms = int(time.time() * 1000)
            window_start_ms = now_ms - (window * 1000)

            async with self.redis_client.pipeline(transaction=True) as pipe:
                # 1. Remove timestamps older than the window
                pipe.zremrangebyscore(key, 0, window_start_ms)
                # 2. Add current timestamp
                pipe.zadd(key, {str(now_ms): now_ms})
                # 3. Count requests in the window
                pipe.zcard(key)
                # 4. Set TTL for the key to avoid memory leaks
                pipe.pexpire(key, window * 1000)
                
                results = await pipe.execute()

            request_count = results[2]  # result of zcard

            if request_count > limit:
                # Limit exceeded, remove the request we just added to prevent endlessly punishing the user
                await self.redis_client.zrem(key, now_ms)
                return False

            return True
        except redis.RedisError as e:
            logger.error(f"Redis rate limiting error (failing open): {e}")
            return True # Fail-open strategy
```

## [app/database/redis.py](file:///home/finkord/dev/rest_api_cnu/app/database/redis.py)

```python
import redis.asyncio as redis
from app.core.config import settings
from typing import Optional

redis_pool: Optional[redis.Redis] = None

def init_redis():
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.aclose()
        redis_pool = None

async def get_redis() -> redis.Redis:
    global redis_pool
    if redis_pool is None:
        init_redis()
    return redis_pool
```

## [app/core/dependencies.py](file:///home/finkord/dev/rest_api_cnu/app/core/dependencies.py)

```python
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
```

## [app/auth/router.py](file:///home/finkord/dev/rest_api_cnu/app/auth/router.py)

```python
from app.core.dependencies import get_auth_service, rate_limit

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: Request, user: UserCreate, service: AuthService = Depends(get_auth_service)):
    await rate_limit(request)
    return await service.register(user)

@router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    # await rate_limit(request)
    return await service.login(form_data)

@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, refresh_request: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)):
    await rate_limit(request)
    return await service.refresh_token(refresh_request)
```

## [app/books/router.py](file:///home/finkord/dev/rest_api_cnu/app/books/router.py)

```python
from app.core.dependencies import (
    get_book_service,
    get_current_user,
    RateLimitDependency
)

router = APIRouter(
    prefix="/api/books",
    tags=["Books"],
    dependencies=[Depends(get_current_user), Depends(RateLimitDependency())]
)
```

## [app/main.py](file:///home/finkord/dev/rest_api_cnu/app/main.py)

```python
from app.database.redis import init_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize connection pools on startup
    init_redis()
    yield
    # Dispose connection pools on shutdown
    await close_redis()
    await engine.dispose()
```

## [app/core/config.py](file:///home/finkord/dev/rest_api_cnu/app/core/config.py)

```python
REDIS_URL: str = "redis://redis:6379/0"
```

## [tests/test_rate_limiter.py](file:///home/finkord/dev/rest_api_cnu/tests/test_rate_limiter.py)

(Entire file content archived)

```python
import pytest
import time
from fastapi.testclient import TestClient
from fastapi import Request

from fastapi import APIRouter, Depends, Request
from app.main import app
from app.core.dependencies import rate_limiter, rate_limit

router = APIRouter()

@router.get("/api/rate_limit_stub")
async def rate_limit_stub_endpoint(request: Request):
    await rate_limit(request)
    return {"status": "ok"}

app.include_router(router)

class MockPipeline:
    def __init__(self, db):
        self.db = db
        self.operations = []
        
    def zremrangebyscore(self, key, min_score, max_score):
        self.operations.append(("zrem", key, min_score, max_score))
        
    def zadd(self, key, mapping):
        self.operations.append(("zadd", key, mapping))
        
    def zcard(self, key):
        self.operations.append(("zcard", key))
        
    def pexpire(self, key, ms):
        self.operations.append(("pexpire", key, ms))
        
    async def execute(self):
        zcard_res = 0
        for op in self.operations:
            cmd = op[0]
            key = op[1]
            if cmd == "zadd":
                if key not in self.db:
                    self.db[key] = []
                for val, score in op[2].items():
                    self.db[key].append(score)
            elif cmd == "zrem":
                if key in self.db:
                    self.db[key] = [v for v in self.db[key] if not (op[2] <= v <= op[3])]
            elif cmd == "zcard":
                zcard_res = len(self.db.get(key, []))
        return [None, None, zcard_res, None]

class AsyncResource:
    def __init__(self, db):
        self.pipe = MockPipeline(db)
    async def __aenter__(self):
        return self.pipe
    async def __aexit__(self, exc_type, exc, tb):
        pass

class MockRedis:
    def __init__(self):
        self.db = {}
        
    def pipeline(self, transaction=True):
        return AsyncResource(self.db)
        
    async def zrem(self, key, *values):
        if key in self.db:
            # self.db[key] is a list of scores
            self.db[key] = [v for v in self.db[key] if v not in values]

@pytest.fixture
def mock_redis_client(mocker):
    mock_client = MockRedis()
    mocker.patch.object(rate_limiter, 'redis_client', mock_client)
    return mock_client

@pytest.fixture
def client(mock_redis_client):
    with TestClient(app) as c:
        yield c

def test_rate_limit_anonymous(client, mocker):
    # Anon limit is 2 per minute
    # First 2 should be 200 OK (hitting books endpoint)
    response = client.get("/api/rate_limit_stub")
    assert response.status_code == 200
    
    response = client.get("/api/rate_limit_stub")
    assert response.status_code == 200
    
    # 3rd should be 429
    response = client.get("/api/rate_limit_stub")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too Many Requests"

def test_rate_limit_authenticated(client, mocker):
    # Mock verify_token_type to simulate valid auth
    mocker.patch("app.core.dependencies.verify_token_type", return_value="1234-5678-9012-3456")
    
    headers = {"Authorization": "Bearer fake_token"}
    
    # Auth limit is 10 per minute
    for _ in range(10):
        response = client.get("/api/rate_limit_stub", headers=headers)
        assert response.status_code == 200

    # 11th should be 429
    response = client.get("/api/rate_limit_stub", headers=headers)
    assert response.status_code == 429
    assert response.json()["detail"] == "Too Many Requests"

def test_rate_limit_reset(client, mocker, mock_redis_client):
    # First 2 requests (anon)
    for _ in range(2):
        assert client.get("/api/rate_limit_stub").status_code == 200
        
    # 3rd request blocked
    assert client.get("/api/rate_limit_stub").status_code == 429

    # Simulate waiting 60 seconds by moving time forward
    # We can mock time.time in the rate limiter module
    original_time = time.time
    mock_time = mocker.patch("app.core.rate_limiter.time.time")
    mock_time.return_value = original_time() + 61

    # Next request should be allowed again
    assert client.get("/api/rate_limit_stub").status_code == 200

def test_rate_limit_x_forwarded_for(client, mocker):
    headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
    
    # First 2 requests (anon, using X-Forwarded-For)
    for _ in range(2):
        assert client.get("/api/rate_limit_stub", headers=headers).status_code == 200
        
    # 3rd request blocked
    response = client.get("/api/rate_limit_stub", headers=headers)
    assert response.status_code == 429
    
    # Request from different IP should be allowed
    headers_diff = {"X-Forwarded-For": "192.168.2.2"}
    assert client.get("/api/rate_limit_stub", headers=headers_diff).status_code == 200

def test_rate_limit_invalid_token(client):
    headers = {"Authorization": "Bearer invalid_token_format"}
    # The request should be rejected immediately as 401 Unauthorized, not fall back to anonymous limit
    response = client.get("/api/rate_limit_stub", headers=headers)
    assert response.status_code == 401

def test_non_punitive_sliding_window(client, mocker, mock_redis_client):
    # Send 3 anonymous requests
    for _ in range(2):
        assert client.get("/api/rate_limit_stub").status_code == 200
    
    # 3rd is blocked, and its timestamp should have been removed
    assert client.get("/api/rate_limit_stub").status_code == 429
    
    # 4th blocked
    assert client.get("/api/rate_limit_stub").status_code == 429
    
    # Mock time to +61 seconds
    original_time = time.time
    mock_time = mocker.patch("app.core.rate_limiter.time.time")
    mock_time.return_value = original_time() + 61
    
    # Now that the window moved, this SHOULD succeed because the previously blocked requests were removed
    # If it was punitive, the 3rd and 4th request timestamps would still exist in the new window, blocking this
    assert client.get("/api/rate_limit_stub").status_code == 200
```
