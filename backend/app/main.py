from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .db import get_pool, close_pool

app = FastAPI(title="HR Search API")

# CORS - frontend będzie na localhost:5173 (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await get_pool()  # Z retry logic

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