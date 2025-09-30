from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from .db import get_pool, close_pool
from .config import settings
from .search import (
    search, autocomplete, search_by_category, search_by_speaker,
    search_by_tags, get_webinar_details, get_categories,
    get_speakers, get_tags, get_popular_tags, list_recent_webinars, get_model
)

class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

app = FastAPI(title="HR Search API", default_response_class=UTF8JSONResponse)

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

# CORS configured via environment (settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
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

@app.get("/api/health/deep")
async def health_deep():
    db_ok = False
    db_error = None
    model_ok = False
    model_error = None
    model_name = settings.EMBEDDING_MODEL
    model_dims = None

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception as e:
        db_error = str(e)

    try:
        model = get_model()
        # Some models expose dimension via helper; fallback to None
        try:
            model_dims = int(getattr(model, "get_sentence_embedding_dimension", lambda: None)() or 0) or None
        except Exception:
            model_dims = None
        model_ok = True
    except Exception as e:
        model_error = str(e)

    status = "ok" if db_ok and model_ok else "degraded"
    return {
        "status": status,
        "db": {"ok": db_ok, "error": db_error},
        "model": {"ok": model_ok, "name": model_name, "dims": model_dims, "error": model_error},
        "config": {
            "semanticThreshold": settings.SEMANTIC_THRESHOLD,
            "fuzzyThreshold": settings.FUZZY_THRESHOLD,
        }
    }

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
    
    # If specific filters are provided, use targeted search with pagination
    if category:
        webinars, total = await search_by_category(category, pool, offset=offset, limit=limit)
    elif speaker:
        webinars, total = await search_by_speaker(speaker, pool, offset=offset, limit=limit)
    elif tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        webinars, total = await search_by_tags(tag_list, pool, offset=offset, limit=limit)
    else:
        # Default: recent webinars with pagination
        webinars, total = await list_recent_webinars(pool, offset=offset, limit=limit)
    
    has_more = (offset + len(webinars)) < total
    
    return {
        "webinars": webinars,
        "total": total,
        "offset": offset,
        "limit": limit,
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