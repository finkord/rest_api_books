from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from app.api import router
from app.database import client

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    client.close()

app = FastAPI(lifespan=lifespan)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
