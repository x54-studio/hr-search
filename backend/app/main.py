from fastapi import FastAPI, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from typing import List, Dict
from .config import settings
from .logging_config import setup_logging, get_logger, set_request_id, get_request_id
from .exceptions import (
    HRSearchException,
    SearchError,
    ValidationError,
)
from .dependencies import (
    dependency_lifespan,
    create_search_service_dependency,
    create_embedding_service_dependency,
    get_database_pool,
)
from .services import SearchService, EmbeddingService

# Setup logging
setup_logging(settings.LOG_LEVEL, "logs/hr_search.log")
logger = get_logger("main")


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper error handling."""
    logger.info(
        "Starting HR Search API",
        extra={
            "version": "1.0.0",
            "log_level": settings.LOG_LEVEL,
            "database_url": settings.DATABASE_URL.split("@")[
                -1
            ],  # Hide credentials
        },
    )

    async with dependency_lifespan(app):
        yield


app = FastAPI(
    title="HR Search API",
    default_response_class=UTF8JSONResponse,
    lifespan=lifespan,
    version="1.0.0",
)

# Create dependency functions after app is created
get_search_service_dependency = create_search_service_dependency(app)
get_embedding_service_dependency = create_embedding_service_dependency(app)

# CORS configured via environment (settings)
# CORS middleware must be added first to handle preflight requests
# before other middleware processes the request
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)



# Global exception handler
@app.exception_handler(HRSearchException)
async def hr_search_exception_handler(
    request: Request, exc: HRSearchException
):
    """Handle custom HR Search exceptions with standardized format."""
    # Get request ID from context or generate one
    request_id = get_request_id() or str(uuid.uuid4())[:8]
    
    # Set request ID on exception if not already set
    if not exc.request_id:
        exc.request_id = request_id
    
    logger.error(
        "HR Search exception occurred",
        extra={
            "error_code": exc.error_code,
            "error_details": exc.details,
            "path": request.url.path,
            "method": request.method,
            "request_id": request_id,
        },
    )

    status_code = 500
    if isinstance(exc, ValidationError):
        status_code = 400
    elif isinstance(exc, SearchError):
        if exc.details.get('search_type') in ['database', 'connection', 'timeout']:
            status_code = 503
        else:
            status_code = 500

    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with standardized format."""
    request_id = get_request_id() or str(uuid.uuid4())[:8]
    
    logger.error(
        "Unhandled exception occurred",
        exc_info=exc,
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "request_id": request_id,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
            "timestamp": time.time(),
            "request_id": request_id,
        },
    )


# Request logging middleware
# This middleware runs after CORS but before route handlers
# It logs all requests and adds request ID for tracing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information and request ID."""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]  # Short request ID for logging

    # Set request ID in context for logging
    set_request_id(request_id)

    # Log request
    logger.info(
        "Request received",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
        },
    )

    try:
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log response
        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_sec": round(process_time, 3),
            },
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            exc_info=e,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "process_time_sec": round(process_time, 3),
            },
        )
        raise


@app.get("/api/health")
async def health():
    """Basic health check endpoint with database verification."""
    try:
        # Get database pool from app state
        pool = get_database_pool(app)

        # Test database connection with a simple query
        start_time = time.time()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_time = time.time() - start_time

        # Check if database response is fast enough (< 100ms)
        db_status = "ok" if db_time < 0.1 else "slow"

        return {
            "status": "ok",
            "timestamp": time.time(),
            "database": {
                "status": db_status,
                "response_time_ms": round(db_time * 1000, 2),
            },
        }
    except Exception as e:
        logger.error("Health check failed", exc_info=e)
        return {
            "status": "degraded",
            "timestamp": time.time(),
            "database": {"status": "error", "error": str(e)},
        }


@app.get("/api/health/pool")
async def health_pool():
    """Check database pool health."""
    try:
        from .dependencies import get_database_pool, get_pool_stats
        
        pool = get_database_pool(app)
        stats = await get_pool_stats(pool)
        
        # Calculate utilization
        utilization = (stats["size"] - stats["idle"]) / stats["max_size"] * 100
        
        return {
            "status": "ok" if utilization < 80 else "warning",
            "pool_stats": stats,
            "utilization_percent": round(utilization, 2),
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error("Pool health check failed", exc_info=e)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time(),
        }


@app.get("/api/metrics/performance")
async def metrics_performance():
    """Get real-time performance metrics."""
    try:
        from .cache import cache
        
        # Get cache statistics
        cache_stats = cache.get_stats()
        
        # Get memory usage
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_usage_mb = process.memory_info().rss / (1024**2)
        except ImportError:
            memory_usage_mb = 0  # psutil not available
        
        # Get pool utilization
        from .dependencies import get_database_pool, get_pool_stats
        pool = get_database_pool(app)
        pool_stats = await get_pool_stats(pool)
        utilization = (pool_stats["size"] - pool_stats["idle"]) / pool_stats["max_size"] * 100
        
        return {
            "timestamp": time.time(),
            "cache_stats": cache_stats,
            "memory_usage_mb": round(memory_usage_mb, 2),
            "pool_utilization_percent": round(utilization, 2),
            "pool_stats": pool_stats,
        }
    except Exception as e:
        logger.error("Performance metrics collection failed", exc_info=e)
        return {
            "timestamp": time.time(),
            "error": str(e),
        }


@app.get("/api/health/deep")
async def health_deep(
    embedding_service: EmbeddingService = Depends(
        get_embedding_service_dependency
    ),
):
    """Deep health check with system status."""
    db_ok = False
    db_error = None
    model_ok = False
    model_error = None
    model_name = settings.EMBEDDING_MODEL
    model_dims = None

    try:
        from .dependencies import get_database_pool

        pool = get_database_pool(app)
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
        logger.debug("Database health check passed")
    except Exception as e:
        db_error = str(e)
        logger.error("Database health check failed", exc_info=e)

    try:
        model = embedding_service.get_model()
        try:
            model_dims = (
                int(
                    getattr(
                        model, "get_sentence_embedding_dimension", lambda: None
                    )()
                    or 0
                )
                or None
            )
        except Exception:
            model_dims = None
        model_ok = True
        logger.debug("Model health check passed")
    except Exception as e:
        model_error = str(e)
        logger.error("Model health check failed", exc_info=e)

    status = "ok" if db_ok and model_ok else "degraded"

    logger.info(
        "Deep health check completed",
        extra={"status": status, "db_ok": db_ok, "model_ok": model_ok},
    )

    return {
        "status": status,
        "db": {"ok": db_ok, "error": db_error},
        "model": {
            "ok": model_ok,
            "name": model_name,
            "dims": model_dims,
            "error": model_error,
        },
        "config": {
            "semanticThreshold": settings.SEMANTIC_THRESHOLD,
            "fuzzyThreshold": settings.FUZZY_THRESHOLD,
        },
    }


@app.get("/api/search")
async def search_endpoint(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = 20,
    debug: bool = False,
    search_service: SearchService = Depends(get_search_service_dependency),
):
    """Search endpoint with proper error handling."""
    if limit < 1 or limit > 50:
        raise ValidationError(
            f"Limit must be between 1 and 50, got {limit}",
            field="limit",
            value=limit,
        )

    try:
        search_response = await search_service.search(q, limit, debug)

        logger.info(
            "Search completed successfully",
            extra={
                "query": q,
                "limit": limit,
                "results_count": search_response["count"],
                "corrected_query": search_response.get("corrected_query"),
                "correction_applied": search_response.get("corrected_query")
                is not None,
                "debug": debug,
            },
        )

        return search_response

    except ValidationError:
        raise
    except SearchError:
        raise
    except Exception as e:
        logger.error(
            "Search endpoint failed",
            exc_info=e,
            extra={"query": q, "limit": limit},
        )
        raise SearchError(f"Search endpoint failed: {str(e)}", query=q)


@app.get("/api/autocomplete")
async def autocomplete_endpoint(
    q: str = Query(..., min_length=1),
    limit: int = 10,
    search_service: SearchService = Depends(get_search_service_dependency),
):
    """Autocomplete endpoint with proper error handling."""
    if limit < 1 or limit > 20:
        raise ValidationError(
            f"Limit must be between 1 and 20, got {limit}",
            field="limit",
            value=limit,
        )

    try:
        suggestions = await search_service.autocomplete(q, limit)

        logger.info(
            "Autocomplete completed successfully",
            extra={
                "query": q,
                "limit": limit,
                "suggestions_count": len(suggestions),
            },
        )

        return {"suggestions": suggestions}

    except ValidationError:
        raise
    except SearchError:
        raise
    except Exception as e:
        logger.error(
            "Autocomplete endpoint failed",
            exc_info=e,
            extra={"query": q, "limit": limit},
        )
        raise SearchError(f"Autocomplete endpoint failed: {str(e)}", query=q)


@app.get("/api/webinars/{webinar_id}")
async def get_webinar(
    webinar_id: str,
    search_service: SearchService = Depends(get_search_service_dependency),
):
    """Get webinar details endpoint with proper error handling."""
    try:
        webinar = await search_service.get_webinar_details(webinar_id)

        logger.info(
            "Webinar details retrieved successfully",
            extra={"webinar_id": webinar_id},
        )

        return webinar

    except SearchError:
        raise
    except Exception as e:
        logger.error(
            "Get webinar endpoint failed",
            exc_info=e,
            extra={"webinar_id": webinar_id},
        )
        raise SearchError(
            f"Get webinar endpoint failed: {str(e)}", query=webinar_id
        )


@app.get("/api/webinars")
async def list_webinars(
    category: str = Query(None),
    speaker: str = Query(None),
    tags: str = Query(None),
    date_range: str = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    search_service: SearchService = Depends(get_search_service_dependency),
):
    """List webinars endpoint with proper error handling."""
    try:
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        webinars, total = await search_service.list_webinars(
            category=category,
            speaker=speaker,
            tags=tag_list,
            date_range=date_range,
            content_type=None,
            offset=offset,
            limit=limit,
        )

        has_more = (offset + len(webinars)) < total

        logger.info(
            "Webinars listed successfully",
            extra={
                "category": category,
                "speaker": speaker,
                "tags": tags,
                "date_range": date_range,
                "offset": offset,
                "limit": limit,
                "webinars_count": len(webinars),
                "total": total,
            },
        )

        return {
            "webinars": webinars,
            "total": total,
            "offset": offset,
            "limit": limit,
            "hasMore": has_more,
        }

    except ValidationError:
        raise
    except SearchError:
        raise
    except Exception as e:
        logger.error(
            "List webinars endpoint failed",
            exc_info=e,
            extra={
                "category": category,
                "speaker": speaker,
                "tags": tags,
                "date_range": date_range,
                "offset": offset,
                "limit": limit,
            },
        )
        raise SearchError(f"List webinars endpoint failed: {str(e)}")


@app.get("/api/categories")
async def list_categories(
    search_service: SearchService = Depends(get_search_service_dependency),
) -> Dict[str, List[Dict]]:
    """List categories endpoint with proper error handling."""
    try:
        categories = await search_service.get_categories()

        logger.info(
            "Categories listed successfully",
            extra={"categories_count": len(categories)},
        )

        return {"categories": categories}

    except SearchError:
        raise
    except Exception as e:
        logger.error("List categories endpoint failed", exc_info=e)
        raise SearchError(f"List categories endpoint failed: {str(e)}")


@app.get("/api/tags")
async def list_tags(
    limit: int = 50,
    search_service: SearchService = Depends(get_search_service_dependency),
) -> Dict[str, List[Dict]]:
    """List tags endpoint with proper error handling."""
    limit = max(1, min(limit, 100))

    try:
        tags = await search_service.get_tags(limit)

        logger.info(
            "Tags listed successfully",
            extra={"limit": limit, "tags_count": len(tags)},
        )

        return {"tags": tags}

    except ValidationError:
        raise
    except SearchError:
        raise
    except Exception as e:
        logger.error(
            "List tags endpoint failed", exc_info=e, extra={"limit": limit}
        )
        raise SearchError(f"List tags endpoint failed: {str(e)}")


@app.get("/api/tags/popular")
async def list_popular_tags(
    limit: int = 20,
    search_service: SearchService = Depends(get_search_service_dependency),
) -> Dict[str, List[Dict]]:
    """List popular tags endpoint with proper error handling."""
    limit = max(1, min(limit, 50))

    try:
        tags = await search_service.get_popular_tags(limit)

        logger.info(
            "Popular tags listed successfully",
            extra={"limit": limit, "tags_count": len(tags)},
        )

        return {"tags": tags}

    except ValidationError:
        raise
    except SearchError:
        raise
    except Exception as e:
        logger.error(
            "List popular tags endpoint failed",
            exc_info=e,
            extra={"limit": limit},
        )
        raise SearchError(f"List popular tags endpoint failed: {str(e)}")


@app.get("/api/speakers")
async def list_speakers(
    limit: int = 50,
    search_service: SearchService = Depends(get_search_service_dependency),
) -> Dict[str, List[Dict]]:
    """List speakers endpoint with proper error handling."""
    limit = max(1, min(limit, 100))

    try:
        speakers = await search_service.get_speakers(limit)

        logger.info(
            "Speakers listed successfully",
            extra={"limit": limit, "speakers_count": len(speakers)},
        )

        return {"speakers": speakers}

    except ValidationError:
        raise
    except SearchError:
        raise
    except Exception as e:
        logger.error(
            "List speakers endpoint failed", exc_info=e, extra={"limit": limit}
        )
        raise SearchError(f"List speakers endpoint failed: {str(e)}")
