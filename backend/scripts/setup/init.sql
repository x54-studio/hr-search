CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- =============================
-- Tables
-- =============================

-- categories
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);

-- speakers
CREATE TABLE IF NOT EXISTS speakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    bio TEXT
);

CREATE INDEX IF NOT EXISTS idx_speakers_name_trgm ON speakers USING GIN(name gin_trgm_ops);

-- tags
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) UNIQUE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tags_slug ON tags(slug);

-- items (was: webinars)
CREATE TABLE IF NOT EXISTS items (
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

CREATE INDEX IF NOT EXISTS idx_items_category ON items(category_id);
CREATE INDEX IF NOT EXISTS idx_items_title_trgm ON items USING GIN(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status) WHERE status = 'published';
CREATE INDEX IF NOT EXISTS idx_items_source_type ON items(source_type);
-- Optimize ordering for recent listings
CREATE INDEX IF NOT EXISTS idx_items_published
ON items(published_date DESC NULLS LAST)
WHERE status = 'published';

-- NOTE: metadata is intentionally unindexed (loose dict, no schema enforcement).
-- Future: CREATE INDEX idx_items_metadata ON items USING GIN(metadata);
-- Add when metadata queries become a bottleneck.

-- item_speakers (many-to-many, was: webinar_speakers)
CREATE TABLE IF NOT EXISTS item_speakers (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    speaker_id UUID REFERENCES speakers(id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, speaker_id)
);

CREATE INDEX IF NOT EXISTS idx_is_speaker ON item_speakers(speaker_id);

-- item_tags (many-to-many, was: webinar_tags)
CREATE TABLE IF NOT EXISTS item_tags (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_it_tag ON item_tags(tag_id);

-- item_embeddings (was: webinar_embeddings)
CREATE TABLE IF NOT EXISTS item_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    embedding_type VARCHAR(20) NOT NULL, -- 'title', 'description', 'audio'
    vector vector(384) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, embedding_type)
);

CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON item_embeddings USING hnsw (vector vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_embeddings_item_id ON item_embeddings(item_id);
