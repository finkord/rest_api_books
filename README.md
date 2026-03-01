# Book Management REST API

This is a simple FastAPI-based REST API for managing books, created for the Programming REST API Course.

## Features

- **Get all books** (`GET /api/books`)
- **Get a specific book** (`GET /api/books/{book_id}`)
- **Create a new book** (`POST /api/books`)
- **Delete a book** (`DELETE /api/books/{book_id}`)
- **Check health status** (`GET /api/health`)

## Development Setup

The project uses `uv` for dependency management. To get started:

### Activate Virtual Environment

```bash
source .venv/bin/activate
```

### Run the Server

You can run the server using `uv` directly or via the `fastapi` CLI:

```bash
# Using Python
uv run main.py

# Using FastAPI CLI
uv run fastapi dev main.py
```

The API will be available at [http://localhost:8000/](http://localhost:8000/).
Interactive documentation (Swagger UI) is automatically generated and available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Run Tests

Tests are written using `pytest`. You can run them using:

```bash
uv run pytest tests.py
```
