from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .db import get_pool, close_pool
from .search import (
    search, autocomplete, search_by_category, search_by_speaker,
    search_by_tags, get_webinar_details, get_categories,
    get_speakers, get_tags, get_popular_tags, list_recent_webinars
)

class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

app = FastAPI(title="HR Search API", default_response_class=UTF8JSONResponse)

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
async def search_endpoint(q: str = Query(..., min_length=1, max_length=200), limit: int = 20, debug: bool = False):
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="Invalid limit")
    
    pool = await get_pool()
    results = await search(q, pool, limit, debug)
    
    return {"results": results, "count": len(results)}

@app.get("/api/autocomplete")
async def autocomplete_endpoint(q: str = Query(..., min_length=1), limit: int = 10):
    if limit < 1 or limit > 20:
        raise HTTPException(status_code=400, detail="Invalid limit")
    
    pool = await get_pool()
    suggestions = await autocomplete(q, pool, limit)
    
    return {"suggestions": suggestions}

@app.get("/api/webinars/{webinar_id}")
async def get_webinar(webinar_id: str):
    pool = await get_pool()
    webinar = await get_webinar_details(webinar_id, pool)
    
    if not webinar:
        raise HTTPException(status_code=404, detail="Webinar not found")
    
    return webinar

@app.get("/api/webinars")
async def list_webinars(
    category: str = Query(None),
    speaker: str = Query(None), 
    tags: str = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    pool = await get_pool()
    
    # If specific filters are provided, use targeted search
    if category:
        results = await search_by_category(category, pool, limit)
    elif speaker:
        results = await search_by_speaker(speaker, pool, limit)
    elif tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        results = await search_by_tags(tag_list, pool, limit)
    else:
        # Default: recent webinars
        results = await list_recent_webinars(pool, limit=limit)
    
    # Apply offset/limit pagination
    paginated_results = results[offset:offset + limit]
    has_more = len(results) > offset + limit
    
    return {
        "webinars": paginated_results,
        "total": len(results),
        "hasMore": has_more
    }

from typing import List, Dict

@app.get("/api/categories")
async def list_categories() -> Dict[str, List[Dict]]:
    pool = await get_pool()
    categories = await get_categories(pool)
    return {"categories": categories}

@app.get("/api/tags")
async def list_tags(limit: int = 100) -> Dict[str, List[Dict]]:
    limit = max(1, min(limit, 500))
    pool = await get_pool()
    tags = await get_tags(pool, limit)
    return {"tags": tags}

@app.get("/api/tags/popular")
async def list_popular_tags(limit: int = 20) -> Dict[str, List[Dict]]:
    limit = max(1, min(limit, 100))
    pool = await get_pool()
    tags = await get_popular_tags(pool, limit)
    return {"tags": tags}

@app.get("/api/speakers")
async def list_speakers(limit: int = 100) -> Dict[str, List[Dict]]:
    limit = max(1, min(limit, 500))
    pool = await get_pool()
    speakers = await get_speakers(pool, limit)
    return {"speakers": speakers}