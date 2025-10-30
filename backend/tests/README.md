# HR Search Backend - Test Suite

## Overview

Simplified test suite for the HR Search backend system covering essential search functionality.

**Current Status**: ✅ **~15-20 essential tests**

## Test Structure

```
backend/tests/
├── conftest.py              # Pytest configuration and fixtures
├── unit/
│   ├── test_embedding_service.py   # Embedding service unit tests
│   └── test_search_service.py       # Search service unit tests
└── integration/
    ├── conftest.py          # Integration test configuration
    └── test_search_flow.py  # End-to-end search flow tests
```

## Running Tests

### Prerequisites
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Ensure database is running
docker-compose up -d db
```

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Search flow tests only
pytest tests/integration/test_search_flow.py
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Tests
```bash
# Run specific test file
pytest tests/unit/test_search_service.py

# Run specific test function
pytest tests/unit/test_search_service.py::TestSearchService::test_search_semantic_success

# Run tests matching pattern
pytest -k "test_search"
```

## Test Categories

### Unit Tests (`tests/unit/`) - ~8 tests total
- **Search Service Tests** (8 tests): Core search functionality
  - Semantic search success
  - Fuzzy search fallback
  - Spell correction
  - Input validation
  - Error handling
  - Autocomplete functionality

- **Embedding Service Tests** (3 tests): ML model management
  - Model lazy loading
  - Embedding generation
  - Input validation
  - Error handling

### Integration Tests (`tests/integration/`) - ~4 tests total
- **Search Flow Tests**: End-to-end search functionality
  - Complete search pipeline testing
  - API endpoint testing
  - Health check testing
  - Integration between all components

## Test Configuration

### Environment Variables
Tests use a separate test database configuration:
```bash
# Optional: Set test database URL
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5431/hr_search_test"
```

### Database Setup
Tests automatically:
- Create test database connections
- Clean up test data after each test
- Validate database schema and extensions

## Test Data

### Fixtures
- **Sample Data**: Realistic test data generators
- **Mock Responses**: Predefined API responses
- **Database Fixtures**: Test data setup and cleanup

### Polish HR Content
Tests include realistic Polish HR content for:
- Semantic search validation
- Language-specific testing
- Real-world scenario testing

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest
```

## Debugging Tests

### Verbose Output
```bash
pytest -v
```

### Debug Mode
```bash
pytest --pdb
```

### Specific Test Debugging
```bash
pytest tests/unit/test_search_service.py::TestSearchService::test_search_semantic_success -v -s
```

## Test Development Patterns

### Simple Mock Setup
```python
@pytest.fixture
def mock_pool():
    """Create a mock database pool."""
    mock_pool = Mock()
    mock_conn = Mock()
    mock_conn.fetchval = AsyncMock(return_value=0)
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.fetchrow = AsyncMock(return_value=None)
    
    # Set up the pool to return our mock connection
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    return mock_pool, mock_conn
```