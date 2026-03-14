"""
Main entry point for the REST API application.
Configures FastAPI app, CORS, lifespans, and routers.
"""
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.models import client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # MongoDB initialization (if needed, e.g. creating indexes) happens here
    yield
    # Close connection on shutdown
    client.close()


app = FastAPI(
    title="Book Management REST API",
    description="A FastAPI-based REST API for managing books with MongoDB",
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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global handler for exceptions.
    Prevents leaking internal database/application errors to the client.
    """
    # In a real app, log the actual exception `exc` using a logger here
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
