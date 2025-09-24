# API Documentation

## Base Configuration

### Base URL
```
Development: http://localhost:8000/api
Production: https://hr-search.mikr.us/api
```

### Headers
```http
Content-Type: application/json
Accept: application/json
```

## Search Endpoints

### 1. Main Search
`GET /api/search`

Semantic search using embeddings with fuzzy fallback.

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| q | string | Yes | Search query (max 200 chars) |
| limit | integer | No | Results limit (default: 20, max: 50) |

**Example Request:**
```bash
curl "http://localhost:8000/api/search?q=rekrutacja%20IT&limit=10"
```

**Success Response (200):**
```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Skuteczna rekrutacja w IT",
      "description": "Jak prowadzić rekrutację specjalistów IT...",
      "category": "Rekrutacja",
      "speakers": ["Jan Kowalski", "Anna Nowak"],
      "tags": ["rekrutacja", "IT", "rozmowa kwalifikacyjna"],
      "duration_ms": 2700000,
      "recorded_date": "2024-01-15",
      "video_url": "https://example.com/video.mp4",
      "pdf_url": "https://example.com/slides.pdf"
    }
  ],
  "count": 10
}
```

**No Results (200):**
```json
{
  "results": [],
  "count": 0,
  "message": "Nie znaleziono wyników"
}
```

**Error Response (400):**
```json
{
  "detail": "Query cannot be empty"
}
```

### 2. Autocomplete
`GET /api/autocomplete`

Real-time suggestions from webinars, speakers, and tags.

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| q | string | Yes | Partial query (min 1 char) |
| limit | integer | No | Max suggestions (default: 10) |

**Example Request:**
```bash
curl "http://localhost:8000/api/autocomplete?q=mot"
```

**Success Response (200):**
```json
{
  "suggestions": [
    {
      "text": "Motywacja pracowników",
      "type": "webinar"
    },
    {
      "text": "Motywowanie zespołu",
      "type": "webinar"
    },
    {
      "text": "motywacja",
      "type": "tag"
    }
  ]
}
```

## Webinar Endpoints

### 3. Get Webinar Details
`GET /api/webinars/{id}`

Get full details of a specific webinar.

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | UUID | Yes | Webinar ID |

**Example Request:**
```bash
curl "http://localhost:8000/api/webinars/550e8400-e29b-41d4-a716-446655440000"
```

**Success Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Skuteczna rekrutacja w IT",
  "description": "Kompleksowy przewodnik po rekrutacji specjalistów IT w 2024 roku...",
  "category": "Rekrutacja",
  "speakers": ["Jan Kowalski", "Anna Nowak"],
  "tags": ["rekrutacja", "IT", "rozmowa kwalifikacyjna"],
  "duration_ms": 2700000,
  "recorded_date": "2024-01-15",
  "video_url": "https://example.com/video.mp4",
  "pdf_url": "https://example.com/slides.pdf"
}
```

**Not Found (404):**
```json
{
  "detail": "Webinar not found"
}
```

### 4. List Webinars
`GET /api/webinars`

List webinars with optional filters.

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| category | string | No | Filter by category slug |
| speaker | string | No | Filter by speaker name |
| tags | string | No | Filter by tag slugs (comma-separated, OR logic) |
| offset | integer | No | Skip first N results (default: 0) |
| limit | integer | No | Max items to return (default: 20, max: 100) |

**Example Request:**
```bash
# First batch
curl "http://localhost:8000/api/webinars?limit=20"

# Load more (next 20)
curl "http://localhost:8000/api/webinars?offset=20&limit=20"
```

**Success Response (200):**
```json
{
  "webinars": [...],
  "total": 45,
  "offset": 20,
  "limit": 20,
  "hasMore": true
}
```

## Metadata Endpoints

### 5. List Categories
`GET /api/categories`

Get all categories with webinar count.

**Example Request:**
```bash
curl "http://localhost:8000/api/categories"
```

**Success Response (200):**
```json
{
  "categories": [
    {
      "slug": "rekrutacja",
      "name": "Rekrutacja",
      "count": 23
    },
    {
      "slug": "onboarding",
      "name": "Onboarding",
      "count": 15
    }
  ]
}
```

### 6. List Speakers
`GET /api/speakers`

Get all speakers with webinar count.

**Example Request:**
```bash
curl "http://localhost:8000/api/speakers"
```

**Success Response (200):**
```json
{
  "speakers": [
    {
      "name": "Jan Kowalski",
      "bio": "Ekspert HR z 15-letnim doświadczeniem",
      "count": 8
    },
    {
      "name": "Anna Nowak",
      "bio": "Specjalistka od rekrutacji IT",
      "count": 5
    }
  ]
}
```

### 7. Popular Tags
`GET /api/tags/popular`

Get most used tags.

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| limit | integer | No | Number of tags (default: 20) |

**Example Request:**
```bash
curl "http://localhost:8000/api/tags/popular?limit=10"
```

**Success Response (200):**
```json
{
  "tags": [
    {
      "slug": "rekrutacja",
      "name": "rekrutacja",
      "count": 45
    },
    {
      "slug": "motywacja",
      "name": "motywacja",
      "count": 32
    }
  ]
}
```

## Error Handling

### Error Response Format
FastAPI automatically returns errors in this format:
```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes
| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

## Performance Expectations

| Endpoint | Target Response Time |
|----------|---------------------|
| /search | < 300ms |
| /autocomplete | < 100ms |
| /webinars/{id} | < 50ms |
| Other endpoints | < 100ms |

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"]
)
```

## Rate Limiting

Not implemented (internal tool for trusted users).

## Authentication

Not required (deployed within company VPN).

## OpenAPI Documentation

FastAPI automatically generates interactive API documentation:
- Development: http://localhost:8000/docs
- Alternative UI: http://localhost:8000/redoc

## Example Usage

### JavaScript
```javascript
async function searchWebinars(query) {
  const params = new URLSearchParams({
    q: query,
    limit: 10
  });
  
  const response = await fetch(
    `http://localhost:8000/api/search?${params}`
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

// Usage
(async () => {
  try {
    const data = await searchWebinars("rekrutacja");
    console.log(`Found ${data.count} webinars`);
    data.results.forEach(webinar => {
      console.log(`- ${webinar.title}`);
    });
  } catch (error) {
    console.error('Search failed:', error);
  }
})();
```

### cURL
```bash
# Search
curl -X GET "http://localhost:8000/api/search?q=motywacja&limit=5"

# Autocomplete
curl -X GET "http://localhost:8000/api/autocomplete?q=rek"

# Get specific webinar
curl -X GET "http://localhost:8000/api/webinars/550e8400-e29b-41d4-a716-446655440000"

# List categories
curl -X GET "http://localhost:8000/api/categories"
```

## Notes

1. All endpoints return JSON
2. All dates are in ISO 8601 format (YYYY-MM-DD)
3. All durations are in milliseconds
4. Empty arrays are returned instead of null
5. UUIDs are returned as strings
