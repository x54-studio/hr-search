# Scripts Directory

Organized scripts for the Search system management.

## Directory Structure

### `setup/` - Database Setup
- `init.sql` - Database schema initialization
- `seed.sql` - Sample data seeding (categories, tags)
- `reset_dev.sh` - Reset development environment (clean DB + reload data)

### `data/` - Data Management
- `generate_sample.py` - Generate sample item data
- `sample_data/` - Sample data files
  - `items.json` - Sample item data
  - `speakers.json` - Sample speaker data

### `maintenance/` - System Maintenance
- `check_database.py` - Database health check
- `clear_embeddings.py` - Clear embedding cache
- `generate_embeddings.py` - Generate embeddings for content
- `optimize_database.py` - Database optimization tasks

### Root Scripts
- `verify_system.py` - Complete system verification
- `test_search.py` - Basic search functionality test
- `test_pagination.py` - Pagination endpoint test

## Quick Start

```bash
# Full reset (from repo root)
./backend/scripts/setup/reset_dev.sh

# Or step by step:
docker compose up -d
cd backend
python scripts/data/generate_sample.py
python scripts/maintenance/generate_embeddings.py
python scripts/verify_system.py
```
