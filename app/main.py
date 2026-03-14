from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.api import router
from app.auth import router as auth_router
from app.models import engine
from app.exceptions import NotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Dispose connection pool on shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail},
    )

app.include_router(auth_router)
app.include_router(router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
