import pytest

pytestmark = pytest.mark.asyncio

async def test_auth_register_and_login(client):
    user_data = {"username": "newuser", "password": "securepassword"}
    reg_response = await client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201
    
    login_data = {"username": "newuser", "password": "securepassword"}
    login_response = await client.post("/api/auth/login", data=login_data)
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

async def test_auth_refresh_token_stateless(client, auth_client_and_tokens):
    _, tokens = auth_client_and_tokens
    refresh_token = tokens["refresh_token"]
    
    response = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["access_token"] != tokens["access_token"]

async def test_logout_invalidates_token(client, auth_client_and_tokens, mock_redis):
    auth_client, tokens = auth_client_and_tokens
    access_token = tokens["access_token"]
    
    mock_redis.exists.return_value = 0
    
    logout_response = await auth_client.post("/api/auth/logout")
    assert logout_response.status_code == 204
    
    assert mock_redis.setex.called
    
    mock_redis.exists.return_value = 1
    
    response = await auth_client.get("/api/books")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has been revoked"

async def test_refresh_token_rotation_blacklisting(client, auth_client_and_tokens, mock_redis):
    _, tokens = auth_client_and_tokens
    refresh_token = tokens["refresh_token"]
    
    mock_redis.exists.return_value = 0
    
    response = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    
    assert mock_redis.setex.called
    
    mock_redis.exists.return_value = 1
    
    response = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has been revoked"
