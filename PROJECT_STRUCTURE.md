# HR Search - Clean Project Structure

## 🏗️ **KISS Architecture**

### **Core Application** (`backend/app/`)
```
app/
├── main.py          # FastAPI application
├── config.py        # Configuration management
├── db.py            # Database connection
└── search.py        # Search algorithms
```

### **Scripts** (`backend/scripts/`)
```
scripts/
├── setup/           # Database initialization
│   ├── init.sql     # Schema setup
│   └── seed.sql     # Sample data
├── data/            # Data management
│   ├── generate_sample.py
│   └── sample_data/
├── maintenance/     # System maintenance
│   ├── check_database.py
│   ├── clear_embeddings.py
│   └── generate_embeddings.py
├── test.py          # Unified test suite
└── README.md        # Scripts documentation
```

### **Documentation** (`docs/`)
```
docs/
├── 01_planning/     # Project planning
├── 02_requirements/ # Requirements analysis
├── 03_design/       # System design
└── 04_implementation/
    ├── CONFIGURATION.md
    ├── SEARCH_IMPLEMENTATION.md
    └── api_documentation.md
```

## 🚀 **Quick Commands**

```bash
# Setup
python scripts/setup/init.sql
python scripts/data/generate_sample.py
python scripts/maintenance/generate_embeddings.py

# Test
python scripts/test.py

# Run
python -m app.main
```

## ✅ **Clean Structure Benefits**

- **KISS**: Simple, logical organization
- **Separation**: Clear purpose for each directory
- **Maintainable**: Easy to find and modify files
- **Scalable**: Room for growth without chaos
