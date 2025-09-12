# Database Schema Design

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

INSERT INTO categories (name, slug) VALUES
    ('Rekrutacja', 'rekrutacja'),
    ('Onboarding', 'onboarding'),
    ('Rozwój pracowników', 'rozwoj'),
    ('Prawo pracy', 'prawo-pracy'),
    ('Wynagrodzenia', 'wynagrodzenia'),
    ('Well-being', 'wellbeing'),
    ('Zarządzanie', 'zarzadzanie');
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

### webinars
```sql
CREATE TABLE webinars (
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

CREATE INDEX idx_webinars_category ON webinars(category_id);
CREATE INDEX idx_webinars_title_trgm ON webinars USING GIN(title gin_trgm_ops);
CREATE INDEX idx_webinars_status ON webinars(status) WHERE status = 'published';
```

### webinar_speakers
```sql
CREATE TABLE webinar_speakers (
    webinar_id UUID REFERENCES webinars(id) ON DELETE CASCADE,
    speaker_id UUID REFERENCES speakers(id) ON DELETE CASCADE,
    PRIMARY KEY (webinar_id, speaker_id)
);

CREATE INDEX idx_ws_speaker ON webinar_speakers(speaker_id);
```

### webinar_tags
```sql
CREATE TABLE webinar_tags (
    webinar_id UUID REFERENCES webinars(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (webinar_id, tag_id)
);

CREATE INDEX idx_wt_tag ON webinar_tags(tag_id);
```

### webinar_embeddings
```sql
CREATE TABLE webinar_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webinar_id UUID REFERENCES webinars(id) ON DELETE CASCADE,
    embedding_type VARCHAR(20) NOT NULL, -- 'title', 'description', 'audio'
    vector vector(384) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(webinar_id, embedding_type)
);

CREATE INDEX idx_embeddings_vector ON webinar_embeddings 
USING hnsw (vector vector_cosine_ops);
```

## Main Queries (No triggers, no search_vector)

### Semantic Search
```sql
SELECT 
    w.*,
    1 - (e.vector <=> $1::vector) as score,
    array_agg(DISTINCT s.name) as speakers,
    array_agg(DISTINCT t.name) as tags
FROM webinars w
JOIN webinar_embeddings e ON w.id = e.webinar_id AND e.embedding_type = 'title'
LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
LEFT JOIN speakers s ON ws.speaker_id = s.id
LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
LEFT JOIN tags t ON wt.tag_id = t.id
WHERE w.status = 'published'
  AND 1 - (e.vector <=> $1::vector) > 0.7
GROUP BY w.id, e.vector
ORDER BY score DESC
LIMIT 20;
```

### Filter by Category + Speaker
```sql
SELECT w.* FROM webinars w
JOIN webinar_speakers ws ON w.id = ws.webinar_id
JOIN speakers s ON ws.speaker_id = s.id
WHERE w.category_id = $1
  AND s.id = $2
  AND w.status = 'published'
ORDER BY w.recorded_date DESC;
```

### Popular Speakers
```sql
SELECT s.name, COUNT(*) as webinar_count
FROM speakers s
JOIN webinar_speakers ws ON s.id = ws.speaker_id
JOIN webinars w ON ws.webinar_id = w.id
WHERE w.status = 'published'
GROUP BY s.id, s.name
ORDER BY webinar_count DESC
LIMIT 10;
```

### Autocomplete (unified)
```sql
-- One query for all suggestions
(
    SELECT title as suggestion, 'webinar' as type, 1 as priority
    FROM webinars
    WHERE title ILIKE $1 || '%' AND status = 'published'
    LIMIT 3
)
UNION ALL
(
    SELECT name as suggestion, 'speaker' as type, 2 as priority
    FROM speakers
    WHERE name ILIKE $1 || '%'
    LIMIT 3
)
UNION ALL
(
    SELECT name as suggestion, 'tag' as type, 3 as priority
    FROM tags
    WHERE name ILIKE $1 || '%'
    LIMIT 3
)
ORDER BY priority, suggestion
LIMIT 10;
```
