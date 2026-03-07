import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from api import router

app = FastAPI()

app.include_router(router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
