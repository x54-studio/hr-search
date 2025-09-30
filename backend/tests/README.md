# HR Search Backend - Test Suite

## Overview

Comprehensive test suite for the HR Search backend system covering unit tests, integration tests, and database operations.

## Test Structure

```
backend/tests/
├── conftest.py              # Pytest configuration and fixtures
├── unit/
│   └── test_search.py      # Search algorithm unit tests
├── integration/
│   ├── test_api.py         # API endpoint integration tests
│   └── test_database.py    # Database integration tests
└── fixtures/
    ├── sample_data.py      # Test data generators
    └── mock_responses.py   # API response mocks
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

# Database tests only
pytest tests/integration/test_database.py

# API tests only
pytest tests/integration/test_api.py
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Tests
```bash
# Run specific test file
pytest tests/unit/test_search.py

# Run specific test function
pytest tests/unit/test_search.py::TestSearch::test_search_empty_query

# Run tests matching pattern
pytest -k "test_search"
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Search Algorithm Tests**: Test core search functionality
  - Embedding generation
  - Semantic search with thresholds
  - Fuzzy search fallback
  - Autocomplete suggestions
  - Category/speaker/tag filtering

### Integration Tests (`tests/integration/`)
- **API Tests**: Test FastAPI endpoints
  - Request/response validation
  - Error handling
  - CORS configuration
  - Parameter validation
  
- **Database Tests**: Test database operations
  - Connection management
  - Schema validation
  - Index performance
  - Constraint validation

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
- Test performance characteristics

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

## Performance Testing

### Database Performance
- Vector similarity query performance (< 100ms)
- Trigram similarity query performance (< 50ms)
- Index validation and optimization

### API Performance
- Response time validation
- Concurrent request handling
- Error response timing

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
pytest tests/unit/test_search.py::TestSearch::test_search_empty_query -v -s
```

## Test Maintenance

### Adding New Tests
1. Create test file in appropriate directory
2. Use existing fixtures from `conftest.py`
3. Follow naming convention: `test_*.py`
4. Add appropriate markers for test categorization

### Test Data Management
- Use fixtures for consistent test data
- Clean up test data in `conftest.py`
- Avoid hardcoded test data in individual tests

### Performance Considerations
- Use `@pytest.mark.slow` for slow tests
- Mock external dependencies when possible
- Use test database for integration tests
