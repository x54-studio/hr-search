# HR Search API Documentation

## Overview

The HR Search API provides semantic search capabilities for HR webinars using machine learning embeddings and fuzzy matching fallback. The API is built with FastAPI and follows RESTful principles with comprehensive error handling.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication (portfolio project). In production, implement proper authentication mechanisms.

## Error Handling

The API uses a consistent error handling pattern with proper HTTP status codes:

| Status Code | Description | Exception Type |
|-------------|-------------|----------------|
| 400 | Bad Request | ValidationError |
| 404 | Not Found | SearchError |
| 500 | Internal Server Error | SearchError |
| 503 | Service Unavailable | SearchError |

### Error Response Format

All API endpoints return standardized error responses with the following format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "additional": "error context"
  },
  "timestamp": 1640995200.123,
  "request_id": "abc12345"
}
```

#### Error Response Fields

- **error**: Machine-readable error code (string)
- **message**: Human-readable error message (string)
- **details**: Additional error context (object)
- **timestamp**: Unix timestamp when error occurred (number)
- **request_id**: Unique request identifier for tracing (string)

#### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `SEARCH_ERROR` | 404/500/503 | Search operation failed |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

#### Error Response Examples

**Validation Error:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Search query too long (max 200 characters)",
  "details": {
    "field": "query",
    "value": "very long query...",
    "max_length": 200
  },
  "timestamp": 1640995200.123,
  "request_id": "abc12345"
}
```

**Resource Not Found:**
```json
{
  "error": "RESOURCE_NOT_FOUND",
  "message": "Webinar not found",
  "details": {
    "resource_type": "webinar",
    "resource_id": "non-existent-id"
  },
  "timestamp": 1640995200.123,
  "request_id": "abc12345"
}
```

**Database Error:**
```json
{
  "error": "DATABASE_ERROR",
  "message": "Database connection failed",
  "details": {
    "operation": "fetch",
    "query": "SELECT * FROM webinars..."
  },
  "timestamp": 1640995200.123,
  "request_id": "abc12345"
}
```

#### Request ID Usage

The `request_id` field is included in all error responses to help with debugging and tracing. You can use this ID to:

1. **Correlate errors with logs**: Search application logs using the request ID
2. **Debug issues**: Reference the request ID when reporting bugs
3. **Track request flow**: Follow a request through multiple services

Example log entry:
```
2024-01-01 12:00:00 ERROR [request_id=abc12345] Database query execution failed: fetch
```

## Endpoints

### Health Check

#### GET /api/health

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /api/health/deep

Comprehensive health check including database and ML model status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": {
    "status": "connected",
    "pool_size": 10,
    "active_connections": 3
  },
  "model": {
    "status": "loaded",
    "name": "paraphrase-multilingual-MiniLM-L12-v2",
    "dimensions": 384
  }
}
```

### Search

#### GET /api/search

Perform spell-corrected semantic search with fuzzy fallback and speaker name search.

**Search Behavior:**
1. **Semantic Search**: Uses ML embeddings to find semantically similar content
2. **Fuzzy Fallback**: If no semantic results, uses fuzzy text matching
3. **Speaker Search**: If no fuzzy results, searches by speaker names (exact and partial matches)

**Parameters:**
- `q` (string, required): Search query (1-200 characters)
- `limit` (integer, optional): Maximum results (default: 20, max: 50)
- `debug` (boolean, optional): Enable debug logging (default: false)

**Example Requests:**
```
# Search by webinar content
GET /api/search?q=leadership development&limit=10

# Search by speaker name (full name)
GET /api/search?q=Agnieszka Kamińska&limit=5

# Search by speaker first name
GET /api/search?q=Agnieszka&limit=10

# Search by speaker last name
GET /api/search?q=Kowalski&limit=5
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "Leadership Development Workshop",
      "description": "Comprehensive leadership training...",
      "duration_ms": 3600000,
      "recorded_date": "2024-01-10T14:00:00Z",
      "video_url": "https://example.com/video.mp4",
      "pdf_url": "https://example.com/slides.pdf",
      "category_name": "Leadership",
      "similarity": 0.85,
      "speakers": ["John Doe", "Jane Smith"],
      "tags": ["leadership", "development", "workshop"]
    }
  ],
  "count": 1,
  "corrected_query": "leadership development",
  "original_query": "leadrship development"
}
```

**Spell Correction:**
- If the system detects a typo and corrects it, `corrected_query` will contain the corrected version
- If no correction is applied, `corrected_query` will be `null`
- The frontend can use this information to show "Did you mean..." suggestions

### Autocomplete

#### GET /api/autocomplete

Get autocomplete suggestions from webinars, speakers, and tags.

**Parameters:**
- `q` (string, required): Partial query text (1-200 characters)
- `limit` (integer, optional): Maximum suggestions (default: 10, max: 20)

**Example Request:**
```
GET /api/autocomplete?q=lead&limit=5
```

**Response:**
```json
{
  "suggestions": [
    {
      "suggestion": "Leadership Development",
      "type": "webinar",
      "priority": 1
    },
    {
      "suggestion": "Leadership Skills",
      "type": "tag",
      "priority": 3
    }
  ]
}
```

### Webinars

#### GET /api/webinars/{webinar_id}

Get detailed information about a specific webinar.

**Parameters:**
- `webinar_id` (string, required): UUID of the webinar

**Example Request:**
```
GET /api/webinars/123e4567-e89b-12d3-a456-426614174000
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Leadership Development Workshop",
  "description": "Comprehensive leadership training...",
  "duration_ms": 3600000,
  "recorded_date": "2024-01-10T14:00:00Z",
  "video_url": "https://example.com/video.mp4",
  "pdf_url": "https://example.com/slides.pdf",
  "status": "published",
  "category_name": "Leadership",
  "speakers": ["John Doe", "Jane Smith"],
  "tags": ["leadership", "development", "workshop"]
}
```

#### GET /api/webinars

List webinars with optional filtering and pagination.

**Parameters:**
- `category` (string, optional): Filter by category slug
- `speaker` (string, optional): Filter by speaker name
- `tags` (string, optional): Comma-separated tag slugs
- `offset` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records (default: 20, max: 50)

**Example Requests:**
```
GET /api/webinars?category=leadership&limit=10
GET /api/webinars?speaker=John Doe&offset=0&limit=20
GET /api/webinars?tags=leadership,development&limit=15
```

**Response:**
```json
{
  "webinars": [
    {
      "id": "uuid",
      "title": "Leadership Development Workshop",
      "description": "Comprehensive leadership training...",
      "duration_ms": 3600000,
      "recorded_date": "2024-01-10T14:00:00Z",
      "video_url": "https://example.com/video.mp4",
      "pdf_url": "https://example.com/slides.pdf",
      "category_name": "Leadership",
      "speakers": ["John Doe", "Jane Smith"],
      "tags": ["leadership", "development", "workshop"]
    }
  ],
  "total_count": 25
}
```

### Categories

#### GET /api/categories

Get all categories with webinar counts.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Leadership",
    "slug": "leadership",
    "description": "Leadership and management topics",
    "webinar_count": 15
  }
]
```

### Tags

#### GET /api/tags

Get all tags with webinar counts.

**Parameters:**
- `limit` (integer, optional): Maximum tags (default: 100, max: 500)

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "leadership",
    "slug": "leadership",
    "webinar_count": 12
  }
]
```

#### GET /api/tags/popular

Get most used tags ordered by usage count.

**Parameters:**
- `limit` (integer, optional): Maximum tags (default: 20, max: 100)

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "leadership",
    "slug": "leadership",
    "webinar_count": 25
  }
]
```

### Speakers

#### GET /api/speakers

Get all speakers with webinar counts.

**Parameters:**
- `limit` (integer, optional): Maximum speakers (default: 100, max: 500)

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "John Doe",
    "bio": "Senior Leadership Consultant",
    "webinar_count": 8
  }
]
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, implement appropriate rate limiting based on your requirements.

## CORS

CORS is configured via environment variables. Default configuration allows all origins for development.

## Logging

The API uses structured JSON logging with the following levels:
- `INFO`: Normal operations
- `WARNING`: Fallback operations (e.g., fuzzy search fallback)
- `ERROR`: Operation failures
- `DEBUG`: Detailed operation information (when debug=true)

## Performance Considerations

- **Spell Correction**: Quick fuzzy pre-check (limit=3) before expensive semantic search
- **Semantic Search**: Uses vector similarity with pgvector extension
- **Fuzzy Search**: Fallback using PostgreSQL trigram matching
- **Connection Pooling**: Database connections are pooled for efficiency
- **Model Caching**: ML models are loaded once and cached in memory
- **Response Times**: Target <300ms for search, <100ms for autocomplete
- **Spell Correction Overhead**: Minimal impact (~10-20ms) due to optimized fuzzy pre-check

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup database
python scripts/setup/init.sql
python scripts/data/generate_sample.py
python scripts/maintenance/generate_embeddings.py

# Run development server
python -m app.main
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/performance/ -v
```

## Architecture

The API follows Clean Architecture principles with:

- **Repository Layer**: Data access abstraction
- **Service Layer**: Business logic encapsulation  
- **API Layer**: HTTP endpoint handling
- **Dependency Injection**: Testable, maintainable code

For detailed architecture documentation, see `docs/04_implementation/REFACTORED_ARCHITECTURE.md`.