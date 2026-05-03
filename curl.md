# Mock API cURL Commands

These commands assume your mock server is running on `http://localhost:4010`. The mock server will return the realistic example data defined in the `openapi.yaml`.

## Authentication

### 1. Register a new user
```bash
curl -X POST http://localhost:4010/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

### 2. Login
Note: This endpoint uses `application/x-www-form-urlencoded` format as required by OAuth2.
```bash
curl -X POST http://localhost:4010/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

### 3. Refresh Token
```bash
curl -X POST http://localhost:4010/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "mock-refresh-token"}'
```

### 4. Logout
Requires the Bearer token returned from the login endpoint.
```bash
curl -X POST http://localhost:4010/api/auth/logout \
  -H "Authorization: Bearer mock-access-token"
```

---

## Books Management

*Note: In the real API, book endpoints require an Authorization header. It is included here for authenticity when testing against the mock server.*

### 5. Get Paginated Books
You can test query parameters like `status`, `author`, `sort_by`, `sort_order`, `limit`, and `offset`.
```bash
curl -X GET "http://localhost:4010/api/books?status=available&limit=10&offset=0" \
  -H "Authorization: Bearer mock-access-token"
```

### 6. Create Multiple Books
The POST endpoint expects an array of book objects.
```bash
curl -X POST http://localhost:4010/api/books \
  -H "Authorization: Bearer mock-access-token" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "title": "The Pragmatic Programmer",
      "author": "David Thomas",
      "description": "Journey to mastery.",
      "status": "available",
      "year_published": 1999
    }
  ]'
```

### 7. Get a Specific Book by ID
Replace the ID with the UUID you want to query.
```bash
curl -X GET http://localhost:4010/api/books/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer mock-access-token"
```

### 8. Delete a Book
```bash
curl -X DELETE http://localhost:4010/api/books/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer mock-access-token"
```
