from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.books.router import router as books_router
from app.auth.router import router as auth_router
from app.core.database import engine
from app.core.exceptions import NotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Dispose connection pool on shutdown
    await engine.dispose()

from app.core.dependencies import RateLimitDependency
from fastapi import Depends

app = FastAPI(lifespan=lifespan, dependencies=[Depends(RateLimitDependency())])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail},
    )

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(books_router)
app.include_router(router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
