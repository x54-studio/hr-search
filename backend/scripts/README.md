# Scripts Directory

Organized scripts for HR Search system management.

## 📁 Directory Structure

### `setup/` - Database Setup
- `init.sql` - Database schema initialization
- `seed.sql` - Sample data seeding

### `data/` - Data Management
- `generate_sample.py` - Generate sample webinar data
- `sample_data/` - Sample data files
  - `webinars.json` - Sample webinar data
  - `speakers.json` - Sample speaker data

### `maintenance/` - System Maintenance
- `check_database.py` - Database health check
- `clear_embeddings.py` - Clear embedding cache
- `generate_embeddings.py` - Generate embeddings for content

### Root Scripts
- `test.py` - Unified test suite (HR + IT terms)
- `test_search.py` - Basic search functionality test

## 🚀 Quick Start

```bash
# 1) Start Postgres (from repo root)
docker compose up -d db

# 2) (Optional) Seed additional sample data
python backend/scripts/data/generate_sample.py

# 3) Generate embeddings
python backend/scripts/maintenance/generate_embeddings.py

# 4) Run tests
python backend/scripts/test.py
```

## 📋 Maintenance Tasks

```bash
# Check database health
python scripts/maintenance/check_database.py

# Clear embeddings (if needed)
python scripts/maintenance/clear_embeddings.py

# Regenerate embeddings
python scripts/maintenance/generate_embeddings.py
```
