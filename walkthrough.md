# Codebase Walkthrough — Book Management REST API

A complete guide to the project's architecture, design decisions, and data flow.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Architecture & Layer Design](#4-architecture--layer-design)
5. [Module Breakdown](#5-module-breakdown)  
   5.1 [models.py — Database & Engine](#51-modelspy--database--engine)  
   5.2 [schemas.py — Input Validation](#52-schemaspy--input-validation)  
   5.3 [repository.py — Data Access](#53-repositorypy--data-access)  
   5.4 [exceptions.py — Custom Errors](#54-exceptionspy--custom-errors)  
   5.5 [services.py — Business Logic](#55-servicespy--business-logic)  
   5.6 [db.py — Session Lifecycle](#56-dbpy--session-lifecycle)  
   5.7 [api.py — HTTP Resources](#57-apipy--http-resources)  
   5.8 [main.py — Application Bootstrap](#58-mainpy--application-bootstrap)  
6. [Request Lifecycle](#6-request-lifecycle)
7. [Database Migrations (Alembic)](#7-database-migrations-alembic)
8. [Infrastructure & Deployment](#8-infrastructure--deployment)
9. [Testing Strategy](#9-testing-strategy)
10. [Environment Variables](#10-environment-variables)

---

## 1. Project Overview

A CRUD REST API for a book collection. Books can be listed with pagination, filtering by `status` or `author`, sorting by `title` or `year_published`, individually fetched, created, and deleted.

**Key architectural properties:**

- **Layered** — HTTP, business logic, and data access are strictly separated
- **Framework-agnostic service layer** — `services.py` has zero Flask imports
- **Request-scoped sessions** — one SQLAlchemy session per HTTP request, cleaned up automatically
- **Schema-validated input** — Pydantic rejects invalid data before it reaches the service layer
- **Alembic-managed schema** — no DDL in application code

---

## 2. Technology Stack

| Concern | Library |
|---|---|
| Web framework | Flask 3.x + Flask-RESTful |
| API documentation | Flasgger (Swagger UI) |
| Input validation | Pydantic v2 |
| ORM | SQLAlchemy 2.x (sync) |
| Database migrations | Alembic |
| Production server | Gunicorn |
| Test runner | pytest |
| Dependency manager | uv |

---

## 3. Project Structure

```
rest_api_cnu/
│
├── app/                        # Application source code
│   ├── __init__.py
│   ├── main.py                 # Flask app factory, error handlers, routes
│   ├── api.py                  # Flask-RESTful resource classes (HTTP layer)
│   ├── services.py             # Business logic (pure Python, no Flask)
│   ├── repository.py           # SQLAlchemy queries (data access layer)
│   ├── models.py               # ORM model + engine + session factory
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── db.py                   # Per-request session management (Flask g)
│   └── exceptions.py           # Custom application exceptions
│
├── alembic/                    # Database migration environment
│   ├── env.py                  # Migration runner (reads DATABASE_URL)
│   ├── script.py.mako          # Migration file template
│   └── versions/               # Generated migration scripts
│
├── tests/
│   └── tests.py                # Full test suite (in-memory SQLite)
│
├── configs/
│   └── psql/                   # Optional PostgreSQL init scripts
│
├── alembic.ini                 # Alembic config
├── docker-compose.yml          # Local dev stack (app + postgres)
├── Dockerfile                  # Production container (gunicorn)
├── pyproject.toml              # Project metadata & dependencies
├── requirements                # Pinned flat dependency list (for Docker)
├── makefile                    # Developer shortcuts
└── .env / .env_example         # Environment configuration
```

---

## 4. Architecture & Layer Design

The application follows a strict **3-layer architecture**. Each layer communicates only with the layer directly below it.

```
┌──────────────────────────────────────────────────────┐
│                    HTTP Layer                        │
│            api.py  (Flask-RESTful Resources)         │
│  • Parses request params / body                      │
│  • Calls Pydantic schemas for input validation       │
│  • Delegates entirely to the service layer           │
│  • Serialises results back to JSON dicts             │
└─────────────────────────┬────────────────────────────┘
                          │ calls
┌─────────────────────────▼────────────────────────────┐
│                  Business Logic Layer                │
│               services.py  (BookService)             │
│  • Orchestrates use-cases (get, create, delete)      │
│  • Builds pagination URLs (urllib.parse)             │
│  • Raises NotFoundError for missing resources        │
│  • No Flask imports whatsoever                       │
└─────────────────────────┬────────────────────────────┘
                          │ calls
┌─────────────────────────▼────────────────────────────┐
│                  Data Access Layer                   │
│              repository.py  (Repository)             │
│  • Executes SQLAlchemy 2.x queries                   │
│  • Accepts / returns ORM model instances             │
│  • No business logic, no HTTP concepts               │
└─────────────────────────┬────────────────────────────┘
                          │ uses
┌─────────────────────────▼────────────────────────────┐
│                     Database                         │
│         models.py  (SQLAlchemy engine + Book)        │
│         alembic/   (schema migration scripts)        │
└──────────────────────────────────────────────────────┘
```

**Cross-cutting concerns** that don't belong to any single layer:

| Concern | Location |
|---|---|
| Session lifecycle | `db.py` + `main.py` teardown |
| Error translation | `main.py` `@errorhandler` |
| Input validation | `schemas.py` (called by `api.py`) |

---

## 5. Module Breakdown

### 5.1 `models.py` — Database & Engine

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
DB_ECHO      = os.getenv("DB_ECHO", "false").lower() == "true"

engine       = create_engine(DATABASE_URL, echo=DB_ECHO)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
```

**`engine`** — a module-level singleton. Created once at import time from `DATABASE_URL`. `echo=False` by default; set `DB_ECHO=true` in the environment to print every SQL statement (useful for debugging).

**`SessionLocal`** — a session *factory*, not a session. Calling `SessionLocal()` creates a new session. `expire_on_commit=False` means ORM objects stay usable after a commit without requiring a new DB round-trip.

**`Book`** — the only ORM model. Uses SQLAlchemy 2.x `Mapped` / `mapped_column` syntax for type-annotated column definitions. Primary key is a `uuid.UUID` auto-generated by Python (not the database).

---

### 5.2 `schemas.py` — Input Validation

Two Pydantic v2 models handle the request/response contract:

**`BookRequest`** — validates incoming POST body:

| Field | Rule |
|---|---|
| `title` | 2–100 chars, no leading `_`, not only whitespace |
| `author` | 2–100 chars, not only whitespace |
| `description` | 2–400 chars, not only whitespace |
| `status` | must be `"available"` or `"borrowed"` |
| `year_published` | integer > 0 and ≤ current year |

If validation fails, Pydantic raises `ValidationError`. `api.py` catches this and returns a `422` response with structured error details — it never reaches the service layer.

**`BookResponse` / `PaginatedBookResponse`** — define the response shape but are not used for serialisation directly; `api.py` manually converts ORM objects to dicts via `_book_to_dict()` so the SQLAlchemy model doesn't need to know about Pydantic.

---

### 5.3 `repository.py` — Data Access

`Repository` wraps all SQL queries behind a clean interface. It receives a `Session` in its constructor, making it straightforward to swap the session in tests.

```python
class Repository:
    def __init__(self, session: Session): ...

    def get_all(self, status, author, sort_by, sort_order, limit, offset)
        -> tuple[list[Book], int]    # books + total count

    def get_by_id(self, book_id: uuid.UUID) -> Book | None
    def create(self, book: Book) -> Book
    def delete(self, book_id: uuid.UUID) -> bool
```

`get_all` runs **two** queries: a `COUNT(*)` subquery for the total (needed for pagination math) and the actual paginated `SELECT` with `LIMIT` / `OFFSET`. Filtering and sorting are applied as `WHERE` / `ORDER BY` clauses on the same base query object.

---

### 5.4 `exceptions.py` — Custom Errors

```python
class NotFoundError(Exception):
    def __init__(self, message: str = "Resource not found"):
        self.message = message
```

A single exception class representing a "resource not found" condition. It carries a `message` attribute consumed by the global error handler in `main.py`.

**Why not `flask.abort(404)`?** — `abort()` is a Flask concept. Calling it inside `services.py` would couple the business logic to the HTTP framework, making it impossible to reuse or unit-test the service layer without a Flask application context. `NotFoundError` is pure Python.

---

### 5.5 `services.py` — Business Logic

`BookService` has exactly zero framework imports. It orchestrates operations using the repository and raises domain exceptions.

**Pagination URL building** uses `urllib.parse.urlencode`:

```python
from urllib.parse import urlencode

def _build_url(lim, off):
    params = {**filter_params, "limit": lim, "offset": off}
    return f"/api/books?{urlencode(params)}"
```

`urlencode` percent-encodes any special characters in filter values (e.g. author names with spaces or ampersands), which string concatenation would not handle safely.

---

### 5.6 `db.py` — Session Lifecycle

```python
def get_db():
    if "db" not in g:
        g.db = SessionLocal()
    return g.db

def teardown_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

**`get_db()`** creates a session on the first call within a request and stores it on Flask's `g` object. Subsequent calls within the same request return the same session — one session per request.

**`teardown_db()`** is registered with `app.teardown_appcontext` in `main.py`, so Flask calls it automatically at the end of every request context regardless of whether an exception occurred. This replaces the old `try/finally session.close()` boilerplate that was repeated in every API method.

---

### 5.7 `api.py` — HTTP Resources

Three Flask-RESTful `Resource` classes:

| Class | Routes | Methods |
|---|---|---|
| `HealthResource` | `/api/health` | `GET` |
| `BookListResource` | `/api/books` | `GET`, `POST` |
| `BookResource` | `/api/books/<book_id>` | `GET`, `DELETE` |

Each method follows the same compact pattern:

```python
def get(self, book_id):
    service = BookService(repository=Repository(get_db()))
    try:
        book_uuid = uuid.UUID(book_id)
    except ValueError:
        return {"message": "Invalid book ID format"}, 400
    book = service.get_book(book_uuid)     # raises NotFoundError if missing
    return _book_to_dict(book), 200
```

1. Build the service with the request-scoped session
2. Parse and validate path/query params
3. Delegate to the service
4. Return a serialised dict with an HTTP status code

`NotFoundError` propagates up to the global `@errorhandler` in `main.py` — no try/except needed inside the resource methods.

Every method includes a YAML docstring consumed by Flasgger to generate the Swagger UI documentation automatically.

---

### 5.8 `main.py` — Application Bootstrap

Responsibilities:

- Creates the `Flask` app instance
- Initialises `Flask-RESTful` (`Api`) and `Flasgger` (`Swagger`)
- Registers routes
- Registers the session teardown: `app.teardown_appcontext(teardown_db)`
- Provides two global error handlers:

```python
@app.errorhandler(HTTPException)     # Werkzeug HTTP errors → JSON
def handle_http_exception(exc): ...

@app.errorhandler(NotFoundError)     # Domain errors → 404 JSON
def handle_not_found(exc): ...
```

`main.py` no longer creates database tables. Schema creation is fully delegated to Alembic.

---

## 6. Request Lifecycle

```
Client
  │
  │ HTTP request
  ▼
Gunicorn (WSGI server)
  │
  ▼
Flask routing  →  api.py Resource method
                      │
                      ├─ get_db()          ← creates Session, stored on g
                      │
                      ├─ BookService(Repository(session))
                      │       │
                      │       ├─ repository.get_all() / get_by_id() / ...
                      │       │         │
                      │       │         └─ SQLAlchemy → PostgreSQL
                      │       │
                      │       └─ raises NotFoundError  ─────────────────┐
                      │                                                  │
                      ├─ _book_to_dict()                                 │
                      │                                                  │
                      └─ return (dict, status_code)                      │
                                                                         │
  @errorhandler(NotFoundError) ◄──────────────────────────────────────── ┘
  returns {"message": "..."}, 404
  │
  │ teardown_appcontext fires
  │ teardown_db() closes session
  ▼
HTTP response → Client
```

---

## 7. Database Migrations (Alembic)

The `alembic/env.py` is configured to:
- Import `Base.metadata` from `app.models` so Alembic knows the full ORM schema
- Override `sqlalchemy.url` with `DATABASE_URL` from the environment at runtime

**Common commands:**

```bash
# Create a new migration (compares models to current DB state)
alembic revision --autogenerate -m "describe change"

# Apply all pending migrations to the DB
alembic upgrade head

# Roll back the last applied migration
alembic downgrade -1

# Show current migration status
alembic current
```

> **No tables are created by application code.** Always run `alembic upgrade head` before starting the app against a fresh database.

---

## 8. Infrastructure & Deployment

### Dockerfile

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim
WORKDIR /code
COPY ./requirements /code/requirements
RUN uv pip install --system --no-cache -r /code/requirements
COPY ./app /code/app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app.main:app"]
```

**Layer ordering** is intentional — `requirements` is copied before `./app` so Docker's build cache is only invalidated on a dependency change, not on every code edit.

**Gunicorn** runs 2 worker processes. For production, the recommended worker count is `(2 × CPU cores) + 1`.

> After updating `pyproject.toml`, always regenerate the pinned requirements file before building:
> ```bash
> uv pip compile pyproject.toml -o requirements
> ```

### Docker Compose

```
app (finkord/books-api:latest)
  └─ depends on: postgres (postgres:16)
  └─ env_file: .env
  └─ port: 8000
  └─ network: books_network

postgres
  └─ data volume: ./data/psql
  └─ init scripts: ./configs/psql/
  └─ network: books_network
```

### Makefile Shortcuts

| Command | Action |
|---|---|
| `make build` | Build Docker image tagged `<branch>_<commit>` |
| `make push` | Push both versioned and `latest` tags to Docker Hub |
| `make compose-up` | Start app + postgres in detached mode |
| `make compose-down` | Stop and remove containers |
| `make compose-up-build` | Start with `--build` (rebuilds the image first) |

---

## 9. Testing Strategy

**`tests/tests.py`** uses pytest with Flask's built-in test client.

### In-Memory SQLite Isolation

```python
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import app.models as _models
_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
_models.engine = _engine
_models.SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)

from app.main import app   # imported AFTER the monkey-patch
```

The engine is patched into `app.models` **before** importing `app.main`, ensuring every layer of the stack uses the in-memory database. No files are created on disk; the schema is wiped and rebuilt between test sessions automatically.

### Fixtures

| Fixture | Scope | Purpose |
|---|---|---|
| `setup_database` | `session` | Creates all tables once; drops them at the end |
| `reset_db_data` | `function` | Clears all rows and inserts a known baseline book before each test |
| `client` | `function` | Provides a Flask test client |

### Coverage

| Area | Test count |
|---|---|
| Health check | 1 |
| List books (basic, pagination, filter, sort) | 6 |
| Get single book (found, not found) | 2 |
| Create book (valid, invalid title/status/year/empty) | 5 |
| Delete book (found, not found) | 2 |
| **Total** | **17** |

```bash
uv run pytest tests/tests.py -v
# 17 passed in ~0.9s
```

---

## 10. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./test.db` | SQLAlchemy connection string for the target database |
| `DB_ECHO` | `false` | Set to `true` to print all SQL statements to stdout |
| `POSTGRES_DB` | *(set in .env)* | PostgreSQL database name (for the compose postgres service) |
| `POSTGRES_USER` | *(set in .env)* | PostgreSQL username |
| `POSTGRES_PASSWORD` | *(set in .env)* | PostgreSQL password |

A `DATABASE_URL` for PostgreSQL follows this format:
```
postgresql://user:password@host:5432/dbname
```
