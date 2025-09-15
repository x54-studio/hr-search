from fastapi import FastAPI, HTTPException, Query
from .db import get_pool, close_pool

app = FastAPI(title="HR Search API")

@app.on_event("startup")
async def startup():
    await get_pool()

@app.on_event("shutdown")
async def shutdown():
    await close_pool()

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/search")
async def search(q: str = Query(..., min_length=1, max_length=200), limit: int = 20):
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="Invalid limit")
    # TODO: implement semantic + fuzzy search
    return {"results": [], "count": 0}