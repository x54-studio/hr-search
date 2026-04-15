# Refactor Decisions

PO decisions from kickoff session (2026-04-15).

## Team

| Role | Responsibility |
|------|---------------|
| **A — Backend Architect** | DB schema, repositories, services, API design |
| **B — Frontend Engineer** | React components, hooks, API client, UI |
| **Q — QA Engineer** | Tests, migration testing, regression prevention |
| **D — DevOps / DBA** | Database, Docker, migration, data pipeline |
| **PO — Product Owner** | Product decisions, scope, priorities |

## Decisions

### Architecture (A)
- **A1**: Big bang rename `webinar` → `item`. One clean pass, no backward compat, no dual endpoints.
- **A2**: Keep `speakers` table name as-is. No rename to `authors`.
- **A3**: `metadata JSONB` — loose dict, no Pydantic validation per source_type.

### Frontend (B)
- **B4**: Minimal UI changes. Clean, no new icons or visual overhaul.
- **B5**: App title configurable from backend (config endpoint).
- **B6**: Replace `content_type: webinar|pdf` filter with `source_type` filter.

### Quality (Q)
- **Q7**: Tests must pass green after every stage. No "fix later" broken tests.
- **Q8**: Old HR seed data (27 webinars) stays as test fixture.
- **Q9**: Integration tests run on new `items` table immediately.

### DevOps (D)
- **D10**: Clean `docker compose down -v` + new `init.sql`. No ALTER TABLE migration.
- **D11**: YouTube data pipeline (yt-dlp → whisper → chunking) is a **separate epic**, not in this refactor scope.
- **D12**: New `init.sql` with `items` table. Old schema preserved in git history only.

### Review decisions (brainstorm session)
- **P1**: URLs per item — `source_url` for primary link + `metadata.pdf_url` for secondary. Flat, no arrays.
- **P2**: Autocomplete type label — `'title'` / `'speaker'` / `'tag'` (source of suggestion, not source_type of item).
- **P3**: source_type filter — hidden when `<= 1` type in data. Appears automatically when new types are added.
- **P4**: Final smoke test — checklist in REFACTOR_PLAN/README.md, not a separate stage or script.
- **P5**: Branching — 1 branch `refactor/generalize-items`, 1 commit per stage.
- **P6**: Dev reset script — `scripts/setup/reset_dev.sh` added in Stage 6.

## Scope boundary

**In scope**: Rename webinar → item, add source_type + metadata JSONB, update all layers, green tests per stage.

**Out of scope**: YouTube pipeline, real data ingestion, Whisper integration, chunk-level search. Those are future epics.
