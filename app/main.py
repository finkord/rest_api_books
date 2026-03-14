from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api import router
from app.models import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Dispose connection pool on shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
