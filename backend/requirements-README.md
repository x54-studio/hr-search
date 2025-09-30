# HR Search Backend - Requirements Management

## Installation

### Production
```bash
pip install -r requirements.txt
```

### Development
```bash
pip install -r requirements-dev.txt
```

## Dependencies Overview

### Production (`requirements.txt`)
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **asyncpg** - PostgreSQL async driver
- **pydantic-settings** - Configuration management
- **sentence-transformers** - ML embeddings
- **requests** - HTTP client

### Development (`requirements-dev.txt`)
- **Testing**: pytest, pytest-asyncio, httpx
- **All production dependencies included**

## Usage

### Local Development
```bash
# Install all dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

### Production Deployment
```bash
# Install only production dependencies
pip install -r requirements.txt

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker
```dockerfile
# Production
COPY requirements.txt .
RUN pip install -r requirements.txt

# Development
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
```
