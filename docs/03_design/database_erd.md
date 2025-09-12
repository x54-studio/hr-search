# Database Entity Relationship Diagram

## ERD Diagram

```mermaid
erDiagram
    categories {
        UUID id PK
        VARCHAR name
        VARCHAR slug UK
    }
    
    speakers {
        UUID id PK
        VARCHAR name UK
        TEXT bio
    }
    
    tags {
        UUID id PK
        VARCHAR name UK
        VARCHAR slug UK
    }
    
    webinars {
        UUID id PK
        VARCHAR title
        TEXT description
        UUID category_id FK
        INTEGER duration_ms
        TEXT video_url
        TEXT pdf_url
        DATE recorded_date
        VARCHAR status
        TIMESTAMP created_at
    }
    
    webinar_speakers {
        UUID webinar_id FK
        UUID speaker_id FK
    }
    
    webinar_tags {
        UUID webinar_id FK
        UUID tag_id FK
    }
    
    webinar_embeddings {
        UUID id PK
        UUID webinar_id FK
        VARCHAR embedding_type
        VECTOR vector
        TIMESTAMP created_at
    }
    
    categories ||--o{ webinars : "has"
    webinars ||--o{ webinar_speakers : "has"
    speakers ||--o{ webinar_speakers : "presents"
    webinars ||--o{ webinar_tags : "has"
    tags ||--o{ webinar_tags : "describes"
    webinars ||--o{ webinar_embeddings : "has"
```

## Table Relationships

### One-to-Many
- **categories → webinars**: Each webinar belongs to one category
- **webinars → webinar_embeddings**: Each webinar can have multiple embedding types

### Many-to-Many (through junction tables)
- **webinars ↔ speakers**: Via `webinar_speakers`
- **webinars ↔ tags**: Via `webinar_tags`

## Data Flow for Search

```mermaid
flowchart TD
    Query[Search Query]
    Query --> Embedding[Generate Embedding]
    
    Embedding --> VectorSearch[Vector Similarity Search]
    VectorSearch --> Embeddings[(webinar_embeddings)]
    
    Query --> TextSearch[Text Search]
    TextSearch --> Webinars[(webinars)]
    
    Query --> FilterSearch[Filter by Category/Speaker/Tag]
    FilterSearch --> Categories[(categories)]
    FilterSearch --> Speakers[(speakers)]
    FilterSearch --> Tags[(tags)]
    
    Embeddings --> Results[Merge Results]
    Webinars --> Results
    Categories --> Results
    Speakers --> Results
    Tags --> Results
    
    Results --> Ranking[Rank by Score]
    Ranking --> Output[Return Top 20]
```

## Index Strategy

```mermaid
graph LR
    subgraph Primary Indexes
        PK1[webinars.id]
        PK2[categories.id]
        PK3[speakers.id]
        PK4[tags.id]
    end
    
    subgraph Search Indexes
        HNSW[embeddings.vector<br/>HNSW Index]
        TRGM1[webinars.title<br/>GIN Trigram]
        TRGM2[speakers.name<br/>GIN Trigram]
    end
    
    subgraph Lookup Indexes
        IDX1[categories.slug]
        IDX2[tags.slug]
        IDX3[webinars.status]
        IDX4[webinars.category_id]
    end
    
    subgraph Junction Indexes
        JX1[webinar_speakers.speaker_id]
        JX2[webinar_tags.tag_id]
    end
```

## Query Patterns

| Query Type | Tables Used | Index Used |
|------------|------------|------------|
| Semantic Search | webinar_embeddings → webinars | HNSW on vector |
| Title Search | webinars | GIN trigram on title |
| By Speaker | webinar_speakers → speakers → webinars | speaker_id index |
| By Category | webinars | category_id index |
| By Tag | webinar_tags → tags → webinars | tag_id index |
| Autocomplete | webinars, speakers, tags | trigram indexes |

## Storage Estimates

```mermaid
pie title "Storage Distribution (Total: ~10MB)"
    "webinars (1000 rows)" : 3
    "embeddings (1000 vectors)" : 4
    "indexes" : 2
    "relations & others" : 1
```

## Notes
- All foreign keys have CASCADE DELETE for data integrity
- UNIQUE constraints prevent duplicate speakers and tags
- Trigram indexes enable fuzzy matching for Polish text
- HNSW index optimized for ~1000 vectors (m=16, ef_construction=64)
