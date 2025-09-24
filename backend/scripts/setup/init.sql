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

-- webinars
CREATE TABLE IF NOT EXISTS webinars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id),
    duration_ms INTEGER,
    video_url TEXT,
    pdf_url TEXT,
    recorded_date DATE,
    status VARCHAR(20) DEFAULT 'published',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('draft', 'published', 'archived'))
);

CREATE INDEX IF NOT EXISTS idx_webinars_category ON webinars(category_id);
CREATE INDEX IF NOT EXISTS idx_webinars_title_trgm ON webinars USING GIN(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_webinars_status ON webinars(status) WHERE status = 'published';
-- Optimize ordering for recent listings
CREATE INDEX IF NOT EXISTS idx_webinars_recorded_published
ON webinars(recorded_date DESC)
WHERE status = 'published';

-- webinar_speakers (many-to-many)
CREATE TABLE IF NOT EXISTS webinar_speakers (
    webinar_id UUID REFERENCES webinars(id) ON DELETE CASCADE,
    speaker_id UUID REFERENCES speakers(id) ON DELETE CASCADE,
    PRIMARY KEY (webinar_id, speaker_id)
);

CREATE INDEX IF NOT EXISTS idx_ws_speaker ON webinar_speakers(speaker_id);

-- webinar_tags (many-to-many)
CREATE TABLE IF NOT EXISTS webinar_tags (
    webinar_id UUID REFERENCES webinars(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (webinar_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_wt_tag ON webinar_tags(tag_id);

-- webinar_embeddings
CREATE TABLE IF NOT EXISTS webinar_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webinar_id UUID REFERENCES webinars(id) ON DELETE CASCADE,
    embedding_type VARCHAR(20) NOT NULL, -- 'title', 'description', 'audio'
    vector vector(384) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(webinar_id, embedding_type)
);

CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON webinar_embeddings USING hnsw (vector vector_cosine_ops);


