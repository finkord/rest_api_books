# Book Management REST API (FastAPI)

A high-performance, asynchronous REST API for managing books, built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**. This project features a robust layered architecture, JWT authentication with refresh token flow, and Alembic for database migrations.

## Features

- **JWT Authentication**: Secure registration, login, and token refresh.
- **Layered Architecture**: Decoupled API, Service, Repository, and Data layers.
- **Database Migrations**: Integrated Alembic for robust schema management.
- **Limit-Offset Pagination**: Optimized queries using the **Deferred Joins** pattern.
- **Unified Error Handling**: Global exception handling with custom domain exceptions.
- **Interactive Documentation**: Swagger UI available at `/docs`.

---

## Project Architecture

- **API Layer (`app/api.py`, `app/auth.py`)**: Endpoints, request parsing, and response formatting.
- **Service Layer (`app/services.py`)**: Business logic and domain rules.
- **Repository Layer (`app/repository.py`)**: Database interaction and complex query logic.
- **Models/Schemas (`app/models.py`, `app/schemas.py`)**: SQLAlchemy models and Pydantic validation schemas.
- **Security (`app/security.py`)**: Password hashing (Bcrypt) and JWT token operations.

---

## Setup & Running

The easiest way to run the API and its PostgreSQL database is using **Docker Compose**.

### Using Docker Compose
1. **Configure Environment**: Create a `.env` file (see `.env_example`).
   ```bash
   cp .env_example .env
   ```
2. **Build and Start**:
   ```bash
   make build
   make compose-up
   ```
3. **Apply Migrations**:
   ```bash
   docker exec -it rest_api_cnu-app-1 uv run alembic upgrade head
   ```

### Local Setup (Without Docker)
1. **Initialize Project**:
   ```bash
   uv sync
   source .venv/bin/activate
   ```
2. **Run Server**:
   ```bash
   uv run fastapi dev app/main.py
   ```

---

## Authentication Workflow

1. **Register**: `POST /api/auth/register`
2. **Login**: `POST /api/auth/login` (Standard form) -> Recive `access_token` & `refresh_token`.
3. **Authorize**: Add `Authorization: Bearer <access_token>` to your headers for book endpoints.
4. **Refresh**: `POST /api/auth/refresh` using the `refresh_token` when the access token expires.

---

## Database Migrations (Alembic)

When you modify `app/models.py`:
- **Generate a new migration**:
  ```bash
  docker exec -it rest_api_cnu-app-1 uv run alembic revision --autogenerate -m "description"
  ```
- **Apply migrations**:
  ```bash
  docker exec -it rest_api_cnu-app-1 uv run alembic upgrade head
  ```

---

## Management & Infrastructure

### Seed Users
To add initial test users to the database:
```bash
docker exec -it rest_api_cnu-app-1 env PYTHONPATH=. python app/seed_users.py
```

### Dependency Management
If you update `pyproject.toml`, compile the new `requirements` file for Docker:
```bash
uv pip compile pyproject.toml -o requirements
```

### Run Tests
```bash
uv run pytest tests/tests.py -v
```

---

## Environment Configuration

| Variable | Description |
| :--- | :--- |
| `DATABASE_URL` | Asyncpg connection string |
| `DB_ECHO` | Enable SQL statement logging |
| `SECRET_KEY` | Key for JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token lifespan |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token lifespan |
