"""
Main entry point for the REST API application.
Configures FastAPI app, CORS, lifespans, and routers.
"""
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api import router
from app.models import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle initialization and teardown of the database connection.
    On startup, tables are created. On shutdown, connection pool is disposed.
    """
    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Dispose connection pool on shutdown
    await engine.dispose()


app = FastAPI(
    title="Book Management REST API",
    description="A FastAPI-based REST API for managing books with PostgreSQL",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Global handler for database exceptions.
    Prevents leaking internal database errors (like SQL queries or structure) to the client.
    """
    # In a real app, log the actual exception `exc` using a logger here
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal database error occurred."},
    )

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
