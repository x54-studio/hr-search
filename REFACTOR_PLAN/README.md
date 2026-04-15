# Refactor Plan: webinar → item generalization

Generalize the HR webinar search engine into a domain-configurable content search engine. The core entity `webinar` becomes `item` with a `source_type` field, supporting future content types (YouTube videos, articles, papers, etc.) without schema changes.

## Stages

| # | Stage | Owner | Depends on | Key deliverable |
|---|-------|-------|------------|-----------------|
| 1 | [DB Schema](01_db_schema.md) | D + A | — | New `items` table with `source_type` + `metadata JSONB` |
| 2 | [Repository](02_repository.md) | A + Q | 1 | `ItemRepository` + updated SQL + unit tests green |
| 3 | [Service + DI](03_service_di.md) | A + Q | 2 | `SearchService` uses `item_repo` + `SearchException` + unit tests green |
| 4 | [API](04_api.md) | A + B + Q | 3 | `/api/items` + `/api/config` + integration tests green |
| 5 | [Frontend](05_frontend.md) | B | 4 | Config-driven title, `source_type` filter, `Item` type, `npm run build` clean |
| 6 | [Scripts](06_scripts.md) | D + A | 4 | Sample data loads as items, embeddings generate, verify_system passes |
| 7 | [Docs](07_docs.md) | A + B | 6 | Technical docs match code, SDLC narrative docs unchanged |

## Execution order

Stages 1–5 are strictly sequential (each layer depends on the one below).
Stage 6 can start after Stage 4 (parallel with Stage 5).
Stage 7 starts after everything else is done.

```
1 → 2 → 3 → 4 → 5
                ↘ → 7
           4 → 6 ↗
```

## Git strategy

Single branch: `refactor/generalize-items` (decision P5).
One commit per stage with conventional prefix: `refactor(db): ...`, `refactor(repo): ...`, etc.

## Rules

- **Tests green after every stage** (decision Q7)
- **No backward compatibility** — clean cut (decision A1)
- **YouTube pipeline is out of scope** — separate epic (decision D11)
- **HR seed data stays** — it's valid domain data, not fake (decision Q8)

## Final verification checklist (decision P4)

Run after all 7 stages are complete:

### Fresh environment
- [ ] `docker compose down -v && docker compose up -d`
- [ ] `python scripts/data/generate_sample.py`
- [ ] `python scripts/maintenance/generate_embeddings.py`
- [ ] `python -m app.main` — backend starts without errors
- [ ] `npm run dev` — frontend starts without errors

### Functional smoke
- [ ] Type "rek" → autocomplete dropdown appears, NO results list below
- [ ] Press Enter → results appear, autocomplete hides
- [ ] Click autocomplete suggestion → results appear for that suggestion
- [ ] Click result → detail view with source_url
- [ ] `GET /api/config` → returns title and source_types
- [ ] `GET /api/items?source_type=webinar` → filtered results
- [ ] `npm run build` → clean, no TypeScript errors
- [ ] `python -m pytest tests/ -v` → all green

### Cleanup
- [ ] `grep -r "webinar" backend/app/` → no results (except comments if any)
- [ ] `grep -r "webinar" frontend/src/ --include="*.ts" --include="*.tsx"` → no results
- [ ] No old `/api/webinars` endpoint responding

## Full decisions log

See [00_decisions.md](00_decisions.md)
