import pytest

pytestmark = pytest.mark.asyncio

async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

async def test_rate_limit_anonymous(client, mock_redis):
    # Anon limit is 2. 
    # 1st request
    mock_redis.pipeline_instance.set_count(1)
    response = await client.get("/api/health") # Health is NOT limited
    assert response.status_code == 200
    
    # 1st book request
    mock_redis.pipeline_instance.set_count(1)
    response = await client.get("/api/books")
    # Anonymous request doesn't need to pass auth to get rate limited!
    
    # 3rd request (exceeding limit of 2)
    mock_redis.pipeline_instance.set_count(3)
    response = await client.get("/api/books")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too Many Requests"

async def test_rate_limit_authenticated(auth_client, auth_client_and_tokens, mock_redis):
    _, tokens = auth_client_and_tokens
    
    # Auth limit is 10.
    # 10th request
    mock_redis.pipeline_instance.set_count(10)
    response = await auth_client.get("/api/books")
    assert response.status_code == 200
    
    # 11th request
    mock_redis.pipeline_instance.set_count(11)
    response = await auth_client.get("/api/books")
    assert response.status_code == 429
