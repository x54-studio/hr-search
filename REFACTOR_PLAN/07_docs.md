# Stage 7: Technical Documentation

**Owner**: A (Backend Architect) + B (Frontend Engineer)
**Depends on**: Stage 6 (all code changes done)
**Branch**: `refactor/07-docs`

## Goal

Update technical reference docs to match new code. SDLC narrative docs (planning, requirements, scenarios) stay as-is — they tell the HR story.

## Docs to update

### `README.md`

- Title/description: mention "domain-configurable semantic search" instead of just "HR webinar search"
- API table: `/api/webinars` → `/api/items`, add `/api/config`
- Keep mention that default domain is HR

### `backend/README.md`

- Structure section: `repositories/item.py` instead of `webinar.py`
- Brief mention of source_type concept

### `CLAUDE.md`

- Architecture section: update file tree (`item.py`, `item_speakers`, etc.)
- Commands section: unchanged (docker, pytest, npm commands are the same)
- Key technical details: mention `source_type`, `metadata JSONB`
- Code conventions: mention that "item" is the generic content entity

### `docs/03_design/database_schema.md`

- Full rewrite of CREATE TABLE statements to match new init.sql
- Update column mapping table
- Update example queries (semantic search, filter, autocomplete)

### `docs/03_design/database_erd.md`

- Update Mermaid ERD: `items`, `item_speakers`, `item_tags`, `item_embeddings`
- Update relationships text
- Update Query Patterns table
- Update Index Strategy diagram

### `docs/04_implementation/api_documentation.md`

- Endpoints: `/api/webinars` → `/api/items`
- Add `/api/config` endpoint docs
- Response examples: update field names (`source_type`, `source_url`, `published_date`, `metadata`)
- Parameter docs: `content_type` → `source_type`

## Docs that stay unchanged

| File | Why |
|------|-----|
| `docs/01_planning/project_scope.md` | HR narrative, SDLC artifact |
| `docs/01_planning/tech_feasibility.md` | HR narrative |
| `docs/02_requirements/functional_requirements.md` | HR narrative |
| `docs/02_requirements/search_scenarios.md` | HR narrative |
| `docs/03_design/architecture.md` | C4 diagrams still valid, HR context is the story |
| `docs/03_design/search_algorithms.md` | Algorithm docs, SQL examples are illustrative |
| `docs/04_implementation/SEARCH_IMPLEMENTATION.md` | Implementation narrative |
| `docs/04_implementation/DATABASE_SIMPLIFICATION.md` | Historical decision doc |
| `docs/04_implementation/tech_stack.md` | Tech justification narrative |
| `docs/glossary.md` | HR terms are the domain glossary |
| `frontend/README.md` | Generic enough already |

## Acceptance criteria

- [ ] README.md API table matches actual endpoints
- [ ] CLAUDE.md architecture matches actual file structure
- [ ] database_schema.md matches actual init.sql
- [ ] database_erd.md Mermaid renders correctly with new table names
- [ ] api_documentation.md matches actual API responses
- [ ] No broken internal doc links
