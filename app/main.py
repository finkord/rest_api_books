"""
Main entry point for the REST API application.
Configures FastAPI app, CORS, lifespans, and routers.
"""
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
