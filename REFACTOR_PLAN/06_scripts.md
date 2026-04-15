# Stage 6: Scripts & Sample Data

**Owner**: D (DevOps/DBA) + A (Backend Architect)
**Depends on**: Stage 4 (API) — scripts use repository/service layer indirectly
**Branch**: `refactor/06-scripts`

## Goal

Update all maintenance scripts, data generation, and sample data to use `items` naming. Keep HR sample data as-is (decision Q8 — it's valid fixture data).

## Changes

### `backend/scripts/data/sample_data/webinars.json`

Rename file to `items.json`. Update structure:

```json
[
  {
    "title": "Rekrutacja w IT w 2024",
    "description": "...",
    "source_type": "webinar",
    "source_url": null,
    "category_slug": "rekrutacja-selekcja",
    "duration_ms": 2700000,
    "published_date": "2024-03-15",
    "metadata": {},
    "speakers": ["Jan Kowalski"],
    "tags": ["rekrutacja", "IT"]
  }
]
```

Fields changed per item:
- Add `source_type: "webinar"` (all existing items are webinars)
- `video_url` → `source_url` (primary link, decision P1)
- `pdf_url` → `metadata: {"pdf_url": "..."}` if non-null, else `metadata: {}` (decision P1)
- Rename `recorded_date` → `published_date`

### `backend/scripts/data/sample_data/speakers.json`

No changes needed — speakers table is unchanged (decision A2).

### `backend/scripts/data/generate_sample.py`

- Read `items.json` instead of `webinars.json`
- SQL: `INSERT INTO items` instead of `INSERT INTO webinars`
- SQL: `INSERT INTO item_speakers` instead of `webinar_speakers`
- SQL: `INSERT INTO item_tags` instead of `webinar_tags`
- Column names: `source_type`, `source_url`, `published_date`, `metadata`
- Log messages: "webinar" → "item"

### `backend/scripts/maintenance/generate_embeddings.py`

- SQL: `FROM items` instead of `FROM webinars`
- SQL: `item_embeddings` instead of `webinar_embeddings`
- SQL: `item_id` instead of `webinar_id`
- Variable names: `webinar` → `item`, `webinars` → `items`
- Log messages update

### `backend/scripts/maintenance/clear_embeddings.py`

- SQL: `DELETE FROM item_embeddings` instead of `webinar_embeddings`

### `backend/scripts/maintenance/optimize_database.py`

- Table references: `items`, `item_speakers`, `item_tags`, `item_embeddings`

### `backend/scripts/maintenance/check_database.py`

- Table checks and SQL references update

### `backend/scripts/maintenance/simplify_indexes.sql`

- Index names: `idx_webinars_*` → `idx_items_*`
- Table references update

### `backend/scripts/verify_system.py`

- API calls: `/api/webinars` → `/api/items`
- Response parsing: `data["webinars"]` → `data["items"]`

### `backend/scripts/test_search.py`, `backend/scripts/test_pagination.py`

- Same pattern: URL and response field updates

### `backend/scripts/README.md`

- Update script descriptions to reference "items" instead of "webinars"

### NEW: `backend/scripts/setup/reset_dev.sh` (decision P6)

```bash
#!/bin/bash
set -e
echo "Resetting development environment..."
docker compose down -v
docker compose up -d
echo "Waiting for PostgreSQL..."
sleep 3
cd backend
source .venv/bin/activate
python scripts/data/generate_sample.py
python scripts/maintenance/generate_embeddings.py
python scripts/verify_system.py
echo "Done. Run 'python -m app.main' to start."
```

- Make executable: `chmod +x scripts/setup/reset_dev.sh`
- Reference in README.md Quick Start section

## Acceptance criteria

- [ ] `python scripts/data/generate_sample.py` — loads HR sample data into `items` table
- [ ] `python scripts/maintenance/generate_embeddings.py` — generates embeddings in `item_embeddings`
- [ ] `python scripts/verify_system.py` — all checks pass
- [ ] `grep -r "webinar" backend/scripts/ --include="*.py" --include="*.sql"` returns nothing
- [ ] All 27 sample items load with `source_type = 'webinar'`
