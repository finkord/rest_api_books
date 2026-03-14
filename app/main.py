from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from app.api import router
from app.models import client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # MongoDB initialization (if needed, e.g. creating indexes) happens here
    yield
    # Close connection on shutdown
    client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
