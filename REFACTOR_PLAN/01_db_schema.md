# Stage 1: Database Schema

**Owner**: D (DevOps/DBA) + A (Backend Architect)
**Depends on**: nothing
**Branch**: `refactor/01-db-schema`

## Goal

Replace `webinars`-centric schema with generic `items` schema. Add `source_type` and `metadata JSONB`.

## Changes

### `backend/scripts/setup/init.sql`

Rewrite from scratch:

```sql
-- Extensions (unchanged)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- categories (unchanged structure)
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL
);

-- speakers (unchanged — decision A2)
CREATE TABLE speakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    bio TEXT
);

-- tags (unchanged structure)
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) UNIQUE NOT NULL
);

-- items (was: webinars)
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50) NOT NULL DEFAULT 'webinar',
    source_url TEXT,                          -- primary link (what user clicks)
    category_id UUID REFERENCES categories(id),
    duration_ms INTEGER,                      -- nullable, only for video/audio
    published_date DATE,                      -- was: recorded_date
    metadata JSONB DEFAULT '{}',              -- source-specific extras (e.g. pdf_url, doi, channel_id)
    status VARCHAR(20) DEFAULT 'published',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('draft', 'published', 'archived'))
);
-- NOTE: metadata is intentionally unindexed (decision A3, loose dict).
-- Future: CREATE INDEX idx_items_metadata ON items USING GIN(metadata);
-- Add when metadata queries become a bottleneck.

-- item_speakers (was: webinar_speakers)
CREATE TABLE item_speakers (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    speaker_id UUID REFERENCES speakers(id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, speaker_id)
);

-- item_tags (was: webinar_tags)
CREATE TABLE item_tags (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, tag_id)
);

-- item_embeddings (was: webinar_embeddings)
CREATE TABLE item_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    embedding_type VARCHAR(20) NOT NULL,
    vector vector(384) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(item_id, embedding_type)
);

-- Indexes (same strategy, renamed)
CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_tags_slug ON tags(slug);
CREATE INDEX idx_speakers_name_trgm ON speakers USING GIN(name gin_trgm_ops);

CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_items_title_trgm ON items USING GIN(title gin_trgm_ops);
CREATE INDEX idx_items_status ON items(status) WHERE status = 'published';
CREATE INDEX idx_items_source_type ON items(source_type);
CREATE INDEX idx_items_published ON items(published_date DESC NULLS LAST)
    WHERE status = 'published';

CREATE INDEX idx_is_speaker ON item_speakers(speaker_id);
CREATE INDEX idx_it_tag ON item_tags(tag_id);

CREATE INDEX idx_embeddings_vector ON item_embeddings
    USING hnsw (vector vector_cosine_ops);
CREATE INDEX idx_embeddings_item_id ON item_embeddings(item_id);
```

### `backend/scripts/setup/seed.sql`

- Categories: **keep HR categories** (they're valid seed data for the HR domain use case).
- Tags: **keep HR tags** (same reason).
- Add `source_type` awareness: existing seed data gets `source_type = 'webinar'`.

### Column mapping

| Old | New | Notes |
|-----|-----|-------|
| `webinars` | `items` | table rename |
| `video_url` | `source_url` | primary link (what user clicks); for webinars this is the video URL |
| `pdf_url` | `metadata.pdf_url` | secondary resource; stored in JSONB (decision P1) |
| `recorded_date` | `published_date` | more generic name |
| — | `source_type` | new: 'webinar', 'youtube', 'article', 'paper', etc. |
| — | `source_url` | new: universal link to original source |
| — | `metadata` | new: JSONB for source-specific fields |
| `webinar_speakers` | `item_speakers` | junction rename |
| `webinar_tags` | `item_tags` | junction rename |
| `webinar_embeddings` | `item_embeddings` | rename, `webinar_id` → `item_id` |

### `docker-compose.yml`

No changes needed. Database name `hr_search` stays (it's the HR domain instance).

## Migration

```bash
docker compose down -v    # destroy old volume (decision D10)
docker compose up -d      # fresh start with new init.sql
```

## Acceptance criteria

- [ ] `docker compose up -d` creates all new tables without errors
- [ ] `\dt` in psql shows: items, item_speakers, item_tags, item_embeddings, categories, speakers, tags
- [ ] Seed data loads (categories + tags)
- [ ] No references to `webinars` table in init.sql or seed.sql
- [ ] Unit tests still pass (they mock DB, don't care about schema)
