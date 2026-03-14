# Book Management REST API

This is a **Flask-based** REST API for managing books, created for the Programming REST API Course. It uses **Flask-RESTful** for resource management, **Flasgger** for Swagger documentation, **SQLAlchemy** (synchronous) for database interactions, and **Alembic** for database migrations.

## Features

- **Get all books** (`GET /api/books?limit=10&offset=0`) — supports limit-offset pagination, filtering, and sorting
- **Get a specific book** (`GET /api/books/<book_id>`)
- **Create a new book** (`POST /api/books`)
- **Delete a book** (`DELETE /api/books/<book_id>`)
- **Check health status** (`GET /api/health`)

## Development Setup

The easiest way to run the API and its database is using Docker Compose.

### Using Docker Compose

Ensure Docker is installed on your machine.

1. Ensure you have a `.env` file in the root directory (see `.env_example`).
2. Start the services:
   ```bash
   docker compose up -d --build
   ```

The API will be available at [http://localhost:8000/](http://localhost:8000/).  
The interactive documentation (Swagger UI) is automatically available at [http://localhost:8000/apidocs/](http://localhost:8000/apidocs/).

> **Note:** The application no longer auto-creates tables on startup. Run the Alembic migrations first (see below).

### Local Setup (Without Docker)

The project uses `uv` for dependency management.

```bash
# Install dependencies
uv sync

# Apply database migrations
uv run alembic upgrade head

# Run the server
uv run python -m app.main
```

*(By default, the application uses a local SQLite database unless `DATABASE_URL` is set in the environment.)*

## Database Migrations (Alembic)

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/). The migration environment reads `DATABASE_URL` from the environment automatically.

```bash
# Create a new migration (autogenerate from models)
uv run alembic revision --autogenerate -m "describe change"

# Apply all pending migrations
uv run alembic upgrade head

# Roll back one migration
uv run alembic downgrade -1
```

## Updating the Requirements File

The `requirements` file is used by the Dockerfile to install dependencies. Regenerate it whenever `pyproject.toml` changes:

```bash
uv pip compile pyproject.toml -o requirements
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./test.db` | SQLAlchemy connection string |
| `DB_ECHO` | `false` | Set to `true` to enable SQL query logging |

## Run Tests

Tests are written using `pytest` and a Flask test client. They use an **in-memory SQLite database** — no files are created on disk.

```bash
uv run pytest tests/tests.py -v
```
