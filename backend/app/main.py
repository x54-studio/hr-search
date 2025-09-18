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

from typing import List, Dict

@app.get("/api/categories")
async def list_categories() -> Dict[str, List[Dict]]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
              c.slug, c.name,
              COALESCE(COUNT(w.id), 0) AS count
            FROM categories c
            LEFT JOIN webinars w ON w.category_id = c.id AND w.status = 'published'
            GROUP BY c.slug, c.name
            ORDER BY c.name
        """)
    return {"categories": [dict(r) for r in rows]}

@app.get("/api/tags")
async def list_tags(limit: int = 100) -> Dict[str, List[Dict]]:
    limit = max(1, min(limit, 500))
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT t.slug, t.name
            FROM tags t
            ORDER BY t.name
            LIMIT $1
        """, limit)
    return {"tags": [dict(r) for r in rows]}

@app.get("/api/speakers")
async def list_speakers(limit: int = 100) -> Dict[str, List[Dict]]:
    limit = max(1, min(limit, 500))
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.name, COALESCE(COUNT(ws.webinar_id), 0) AS count
            FROM speakers s
            LEFT JOIN webinar_speakers ws ON ws.speaker_id = s.id
            LEFT JOIN webinars w ON w.id = ws.webinar_id AND w.status = 'published'
            GROUP BY s.name
            ORDER BY s.name
            LIMIT $1
        """, limit)
    return {"speakers": [dict(r) for r in rows]}