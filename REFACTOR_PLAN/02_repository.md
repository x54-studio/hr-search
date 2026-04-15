# Stage 2: Repository Layer

**Owner**: A (Backend Architect) + Q (QA Engineer)
**Depends on**: Stage 1 (DB schema)
**Branch**: `refactor/02-repository`

## Goal

Rename `WebinarRepository` → `ItemRepository`. Update all SQL to reference new table names. Update unit tests in the same pass (Q7: green after every stage).

## Changes

### Rename files

| Old | New |
|-----|-----|
| `backend/app/repositories/webinar.py` | `backend/app/repositories/item.py` |

### `backend/app/repositories/item.py` (was webinar.py)

- Class: `WebinarRepository` → `ItemRepository`
- All SQL: `webinars w` → `items i`, `webinar_speakers` → `item_speakers`, `webinar_tags` → `item_tags`, `webinar_embeddings` → `item_embeddings`
- Column: `w.recorded_date` → `i.published_date`
- Column: `w.video_url, w.pdf_url` → `i.source_url, i.source_type, i.metadata`
- Alias: `w.` → `i.` throughout
- `_get_content_type_condition()` → `_get_source_type_condition()`:
  - Old: checks `video_url IS NOT NULL` / `pdf_url IS NOT NULL`
  - New: checks `source_type = $N` (parameterized)
- Method `get_by_id()`: error message `"Webinar not found"` → `"Item not found"`
- Return shape: `source_url` (primary link) returned directly; `metadata` returned as JSONB (frontend extracts `pdf_url` etc.)
- SELECT columns: `i.source_url, i.source_type, i.metadata` instead of `w.video_url, w.pdf_url`

### `backend/app/repositories/category.py`

- SQL references: `webinars` → `items`, `webinar_speakers` → `item_speakers`, `webinar_tags` → `item_tags`
- Autocomplete suggestion type: `'webinar'` → `'title'` (decision P2 — label describes source of suggestion, not source_type)
- **SQL alias**: `COUNT(*) as webinar_count` → `COUNT(*) as item_count` in categories, speakers, tags queries

### `backend/app/repositories/embedding.py`

- SQL: `webinar_embeddings` → `item_embeddings`, `webinar_id` → `item_id`
- Class name if present: `EmbeddingRepository` (probably unchanged, check)

### `backend/app/repositories/__init__.py`

- Export: `WebinarRepository` → `ItemRepository`

### Unit tests: `backend/tests/unit/test_search_service.py`

- Update mock repository key: `'webinar_repo'` → `'item_repo'`
- Update `SearchService` constructor arg: `webinar_repo=` → `item_repo=`
- Update `mock_repositories['webinar_repo']` → `mock_repositories['item_repo']`
- Mock method calls: `item_repo.search_semantic`, `item_repo.search_fuzzy`, etc.

### Fixtures: `backend/tests/conftest.py`

- `sample_webinar_data` → `sample_item_data`
- Fields: add `source_type`, `source_url`, `metadata: {"pdf_url": "..."}` (decision P1); remove `video_url`, `pdf_url`; rename `recorded_date` → `published_date`
- `sample_search_results`: update field names

## Key SQL change example

```sql
-- Before
FROM webinars w
LEFT JOIN categories c ON w.category_id = c.id
LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
LEFT JOIN speakers s ON ws.speaker_id = s.id

-- After
FROM items i
LEFT JOIN categories c ON i.category_id = c.id
LEFT JOIN item_speakers isp ON i.id = isp.item_id
LEFT JOIN speakers s ON isp.speaker_id = s.id
```

## source_type filter (replaces content_type)

```python
def _get_source_type_condition(self, source_type: Optional[str]) -> str:
    if source_type:
        return " AND i.source_type = ${param}"
    return ""
```

## Acceptance criteria

- [ ] `python -m pytest tests/unit/ -v` — all green
- [ ] No references to `WebinarRepository` anywhere in `app/`
- [ ] No SQL referencing `webinars`, `webinar_speakers`, `webinar_tags`, `webinar_embeddings` tables
- [ ] `grep -r "webinar" backend/app/repositories/` returns nothing
