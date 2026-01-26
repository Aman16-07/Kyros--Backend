"""Application entrypoint (placeholder)."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"status": "backend skeleton"}
