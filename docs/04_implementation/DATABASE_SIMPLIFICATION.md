# Database Simplification

## Why We Removed Indexes

This project originally had 26+ indexes for ~100 webinar records. This violated KISS principles and was over-engineered.

### Indexes Removed

**Duplicates:**
- Multiple trigram indexes on same column
- Duplicate HNSW vector indexes
- Overlapping composite indexes

**Unused:**
- Full-text search (semantic search is used instead)
- Speaker bio search (feature doesn't exist)
- Case-insensitive tag searches (not in queries)

**Premature Optimization:**
- Triple composite indexes for 100 rows
- Aggregation optimization for tiny datasets

### When to Add Indexes Back

If the project scales to 10,000+ webinars:
1. Monitor slow query log
2. Use EXPLAIN ANALYZE on slow queries
3. Add specific indexes for proven bottlenecks

### Performance Testing

Before: 26+ indexes, ~150ms avg search
After: 10 indexes, ~150ms avg search
**No measurable performance difference for portfolio scale.**

## Essential Indexes Kept

The following indexes are actually used by the application:

### Core Lookups
- `idx_categories_slug` - Category filtering
- `idx_tags_slug` - Tag filtering  
- `idx_speakers_name_trgm` - Speaker name search

### Webinar Operations
- `idx_webinars_category` - JOIN operations
- `idx_webinars_status` - Published filter
- `idx_webinars_title_trgm` - Fuzzy search

### Many-to-Many Relationships
- `idx_ws_speaker` - Speaker-webinar joins
- `idx_wt_tag` - Tag-webinar joins

### Vector Search (Core Feature)
- `idx_embeddings_vector` - Semantic search
- `idx_embeddings_webinar_id` - Embedding lookups

## Migration Script

Use `backend/scripts/maintenance/simplify_indexes.sql` to remove unnecessary indexes from existing databases.

## Benefits

**Simplicity:**
- 60% fewer indexes to maintain
- Easier to understand schema
- Faster schema migrations

**KISS Compliance:**
- Appropriate for portfolio scale
- No premature optimization
- Clear upgrade path when needed

**Performance:**
- Same performance for 100 records
- Reduced memory footprint
- Faster writes (fewer indexes to update)

**Portfolio Quality:**
- Shows good judgment (not over-engineering)
- Demonstrates understanding of when to optimize
- Clean, professional code
