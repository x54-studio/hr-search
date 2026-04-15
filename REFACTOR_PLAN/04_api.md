# Stage 4: API Endpoints

**Owner**: A (Backend Architect) + B (Frontend Engineer) + Q (QA Engineer)
**Depends on**: Stage 3 (Service + DI)
**Branch**: `refactor/04-api`

## Goal

Replace `/api/webinars` endpoints with `/api/items`. Add `/api/config` endpoint for frontend-configurable domain title. Update integration tests.

## Changes

### `backend/app/main.py`

#### Rename endpoints

| Old | New |
|-----|-----|
| `GET /api/webinars/{webinar_id}` | `GET /api/items/{item_id}` |
| `GET /api/webinars` | `GET /api/items` |

#### Rename functions

| Old | New |
|-----|-----|
| `get_webinar()` | `get_item()` |
| `list_webinars()` | `list_items()` |

#### Parameter rename

| Old | New |
|-----|-----|
| `webinar_id: str` | `item_id: str` |
| `content_type: Optional[str]` | `source_type: Optional[str]` |

#### New endpoint: `/api/config` (decision B5)

```python
@app.get("/api/config")
async def get_config():
    """Public config for frontend (domain title, available source types, etc.)."""
    return {
        "title": settings.DOMAIN_TITLE,
        "source_types": ["webinar", "youtube", "article", "paper"],
    }
```

Frontend uses this for the page title and to conditionally show the source_type filter (decision P3: hidden when <= 1 type).

#### Response shape changes

Old `/api/webinars` response:
```json
{
  "webinars": [...],
  "total": 25,
  "offset": 0,
  "limit": 20,
  "has_more": true
}
```

New `/api/items` response:
```json
{
  "items": [...],
  "total": 25,
  "offset": 0,
  "limit": 20,
  "has_more": true
}
```

Each item object:
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "source_type": "webinar",
  "source_url": "https://example.com/video.mp4",
  "duration_ms": 3600000,
  "published_date": "2024-01-10",
  "metadata": {"pdf_url": "https://example.com/slides.pdf"},
  "category_name": "Rekrutacja",
  "speakers": ["Jan Kowalski"],
  "tags": ["rekrutacja", "IT"],
  "similarity": 0.85
}
```

Autocomplete suggestion type labels (decision P2):
```json
{"suggestion": "Rekrutacja w IT", "type": "title"},
{"suggestion": "Jan Kowalski", "type": "speaker"},
{"suggestion": "rekrutacja", "type": "tag"}
```
```

#### Metadata endpoint responses

`/api/categories`, `/api/speakers`, `/api/tags`, `/api/tags/popular` — rename response field:
- `webinar_count` → `item_count`

#### Exception handler

```python
@app.exception_handler(SearchException)   # was HRSearchException
async def search_exception_handler(request, exc):
    ...
```

#### Log messages

- `"Starting HR Search API"` → `"Starting Search API"`
- `"HR Search exception occurred"` → `"Search exception occurred"`
- Title in FastAPI app: `title="HR Search API"` → `title=settings.DOMAIN_TITLE + " API"`

#### content_type → source_type in query params

Old: `content_type: Optional[str] = Query(None, regex="^(webinar|pdf)$")`
New: `source_type: Optional[str] = Query(None)` (no regex — loose, new types can be added freely)

### Integration tests: `backend/tests/integration/test_search_flow.py`

- `GET /api/webinars` → `GET /api/items`
- `data["webinars"]` → `data["items"]`
- `content_type` → `source_type` in query params
- Add test for `GET /api/config` endpoint
- All other assertions (status codes, response shape) stay structurally the same

## Acceptance criteria

- [ ] `python -m pytest tests/unit/ -v` — all green
- [ ] `python -m pytest tests/integration/ -v` — all green (requires running DB with new schema)
- [ ] `curl /api/items` returns items (not webinars)
- [ ] `curl /api/items/{id}` returns single item
- [ ] `curl /api/config` returns `{"title": "HR Knowledge Search", "source_types": [...]}`
- [ ] `curl /api/webinars` returns 404 (no backward compat, decision A1)
- [ ] `grep -r "webinar" backend/app/main.py` returns nothing (except maybe comments referencing migration)
