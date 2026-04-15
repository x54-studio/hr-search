# Stage 3: Service + DI Layer

**Owner**: A (Backend Architect) + Q (QA Engineer)
**Depends on**: Stage 2 (Repository)
**Branch**: `refactor/03-service-di`

## Goal

Update SearchService, EmbeddingService, DI container, exceptions, and config to use `item` naming. Update unit tests in same pass.

## Changes

### `backend/app/services/search_service.py`

- Import: `WebinarRepository` → `ItemRepository`
- Constructor param: `webinar_repo` → `item_repo`
- All `self.webinar_repo` → `self.item_repo`
- Method names if webinar-specific: `get_webinar_details()` → `get_item_details()`
- Method: `list_webinars()` → `list_items()`
- Log messages: `"Webinar details retrieved"` → `"Item details retrieved"`, etc.
- Parameter: `content_type` → `source_type` in method signatures

### `backend/app/services/embedding_service.py`

- Check for any `webinar` references in log messages or comments
- Likely minimal changes — embedding logic is already generic

### `backend/app/dependencies.py`

- Import: `WebinarRepository` → `ItemRepository`
- DI wiring: `WebinarRepository(pool)` → `ItemRepository(pool)`
- Constructor arg to SearchService: `webinar_repo=` → `item_repo=`

### `backend/app/exceptions.py`

- `HRSearchException` → `SearchException`
- All subclasses that reference HR: update naming
- Check if exception messages mention "webinar"

### `backend/app/config.py`

- Add: `DOMAIN_TITLE: str = Field(default="HR Knowledge Search", description="Display title for the application")`
- Database URL default stays `hr_search` (it's the HR instance)

### `backend/app/logging_config.py`

- Log file: `"logs/hr_search.log"` — keep or rename to `"logs/search.log"`? 
  - Recommendation: keep as-is, it's the HR instance log

### `backend/app/cache/__init__.py`

- Check for webinar references (likely none in cache logic)

### Unit tests: `backend/tests/unit/test_search_service.py`

- Already updated repo mocks in Stage 2
- Update method calls: `search_service.get_webinar_details()` → `search_service.get_item_details()`
- Update method calls: `search_service.list_webinars()` → `search_service.list_items()`

### Integration test fixtures: `backend/tests/integration/conftest.py`

- Check for webinar references, update if present

## Acceptance criteria

- [ ] `python -m pytest tests/unit/ -v` — all green
- [ ] `grep -r "webinar" backend/app/services/` returns nothing
- [ ] `grep -r "webinar" backend/app/dependencies.py` returns nothing
- [ ] `grep -r "HRSearchException" backend/app/` returns nothing
- [ ] Import chain works: `item.py` → `__init__.py` → `dependencies.py` → `search_service.py` → `main.py`
