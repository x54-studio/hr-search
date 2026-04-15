# Database Schema Design

> **Note**: This schema has been simplified to follow KISS principles. See [DATABASE_SIMPLIFICATION.md](../04_implementation/DATABASE_SIMPLIFICATION.md) for details on removed indexes.

## Extensions
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
```

## Core Tables

### categories
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL
);

CREATE INDEX idx_categories_slug ON categories(slug);
```

### speakers
```sql
CREATE TABLE speakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    bio TEXT
);

CREATE INDEX idx_speakers_name_trgm ON speakers USING GIN(name gin_trgm_ops);
```

### tags
```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) UNIQUE NOT NULL
);

CREATE INDEX idx_tags_slug ON tags(slug);
```

### items
```sql
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50) NOT NULL DEFAULT 'webinar',
    source_url TEXT,
    category_id UUID REFERENCES categories(id),
    duration_ms INTEGER,
    published_date DATE,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'published',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('draft', 'published', 'archived'))
);

CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_items_title_trgm ON items USING GIN(title gin_trgm_ops);
CREATE INDEX idx_items_status ON items(status) WHERE status = 'published';
CREATE INDEX idx_items_source_type ON items(source_type);
CREATE INDEX idx_items_published ON items(published_date DESC NULLS LAST)
    WHERE status = 'published';
```

### item_speakers
```sql
CREATE TABLE item_speakers (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    speaker_id UUID REFERENCES speakers(id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, speaker_id)
);

CREATE INDEX idx_is_speaker ON item_speakers(speaker_id);
```

### item_tags
```sql
CREATE TABLE item_tags (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, tag_id)
);

CREATE INDEX idx_it_tag ON item_tags(tag_id);
```

### item_embeddings
```sql
CREATE TABLE item_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    embedding_type VARCHAR(20) NOT NULL,
    vector vector(384) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(item_id, embedding_type)
);

CREATE INDEX idx_embeddings_vector ON item_embeddings
USING hnsw (vector vector_cosine_ops);
```

## Main Queries

### Semantic Search
```sql
SELECT
    i.*, 1 - (e.vector <=> $1::vector) as score,
    array_agg(DISTINCT s.name) as speakers,
    array_agg(DISTINCT t.name) as tags
FROM items i
JOIN item_embeddings e ON i.id = e.item_id AND e.embedding_type = 'title'
LEFT JOIN item_speakers isp ON i.id = isp.item_id
LEFT JOIN speakers s ON isp.speaker_id = s.id
LEFT JOIN item_tags it ON i.id = it.item_id
LEFT JOIN tags t ON it.tag_id = t.id
WHERE i.status = 'published'
  AND 1 - (e.vector <=> $1::vector) > 0.7
GROUP BY i.id, e.vector
ORDER BY score DESC
LIMIT 20;
```

### Autocomplete (unified)
```sql
(
    SELECT title as suggestion, 'title' as type, 1 as priority
    FROM items
    WHERE title ILIKE $1 || '%' AND status = 'published'
    LIMIT 3
)
UNION ALL
(
    SELECT name as suggestion, 'speaker' as type, 2 as priority
    FROM speakers WHERE name ILIKE $1 || '%'
    LIMIT 3
)
UNION ALL
(
    SELECT name as suggestion, 'tag' as type, 3 as priority
    FROM tags WHERE name ILIKE $1 || '%'
    LIMIT 3
)
ORDER BY priority, suggestion
LIMIT 10;
```
