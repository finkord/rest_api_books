# Book Management REST API

This is a FastAPI-based REST API for managing books, created for the Programming REST API Course. It integrates PostgreSQL via SQLAlchemy and provides Limit-Offset pagination.

## Features

- **Get all books** (`GET /api/books?limit=10&offset=0`) - Supports Limit-Offset pagination
- **Get a specific book** (`GET /api/books/{book_id}`)
- **Create a new book** (`POST /api/books`)
- **Delete a book** (`DELETE /api/books/{book_id}`)
- **Check health status** (`GET /api/health`)

## Development Setup

The easiest way to run the API and its PostgreSQL database is using Docker Compose.

### Using Docker Compose

Ensure Docker is installed on your machine.

1. Ensure you have a `.env` file in the root directory containing your database credentials.
2. Start the services:
   ```bash
   docker compose up -d --build
   ```

The API will be available at [http://localhost:8000/](http://localhost:8000/).
Interactive documentation (Swagger UI) is automatically generated and available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Local Setup (Without Docker)

The project uses `uv` for dependency management. If you want to run it locally without Docker:

```bash
# Activate Virtual Environment
source .venv/bin/activate

# Install dependencies
uv sync

# Run the Server
uv run fastapi dev app/main.py
```
*(By default, running locally without a `.env` configured for PostgreSQL will fall back to using a local SQLite database).*

### Run Tests

Tests are written using `pytest` and use an isolated local SQLite database to prevent interfering with your main PostgreSQL data. You can run them using `uv`:

```bash
uv run pytest tests/tests.py
```
