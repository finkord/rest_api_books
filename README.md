# Book Management REST API

This is a **Flask-based** REST API for managing books, created for the Programming REST API Course. It uses **Flask-RESTful** for resource management, **Flasgger** for Swagger documentation, and **SQLAlchemy** (synchronous) for database interactions.

## Features

- **Get all books** (`GET /api/books?limit=10&offset=0`) - Supports Limit-Offset pagination
- **Get a specific book** (`GET /api/books/<book_id>`)
- **Create a new book** (`POST /api/books`)
- **Delete a book** (`DELETE /api/books/<book_id>`)
- **Check health status** (`GET /api/health`)

## Development Setup

The easiest way to run the API and its database is using Docker Compose.

### Using Docker Compose

Ensure Docker is installed on your machine.

1. Ensure you have a `.env` file in the root directory.
2. Start the services:
   ```bash
   docker compose up -d --build
   ```

The API will be available at [http://localhost:8000/](http://localhost:8000/).
The interactive documentation (Swagger UI) is automatically available at [http://localhost:8000/apidocs/](http://localhost:8000/apidocs/).

### Local Setup (Without Docker)

The project uses `uv` for dependency management. To run it locally:

```bash
# Install dependencies
uv sync

# Run the Server
uv run python -m app.main
```
*(By default, the application uses a local SQLite database `test.db` unless a `DATABASE_URL` is provided in the environment).*

### Run Tests

Tests are written using `pytest` and a Flask test client. They use an isolated local SQLite database.

```bash
uv run pytest tests/tests.py
```
