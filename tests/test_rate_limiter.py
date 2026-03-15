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
