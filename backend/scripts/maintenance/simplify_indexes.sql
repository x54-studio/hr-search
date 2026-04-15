-- Database Index Simplification Migration
-- Removes over-engineered indexes for portfolio project with ~100 items
-- Reduces from 26+ indexes to 10 essential indexes

-- Drop duplicate indexes
DROP INDEX IF EXISTS idx_items_title_gin;  -- Duplicate of idx_items_title_trgm
DROP INDEX IF EXISTS idx_embeddings_vector_cosine;  -- Duplicate of idx_embeddings_vector

-- Drop unused indexes (never queried)
DROP INDEX IF EXISTS idx_speakers_bio_gin;
DROP INDEX IF EXISTS idx_tags_name_gin;
DROP INDEX IF EXISTS idx_items_search_polish;
DROP INDEX IF EXISTS idx_speakers_name_lower;
DROP INDEX IF EXISTS idx_tags_name_lower;

-- Drop over-optimized composite indexes
DROP INDEX IF EXISTS idx_embeddings_type_item;
DROP INDEX IF EXISTS idx_item_tags_tag_item;
DROP INDEX IF EXISTS idx_item_speakers_speaker_item;
DROP INDEX IF EXISTS idx_items_category_date_published;
DROP INDEX IF EXISTS idx_items_published;
DROP INDEX IF EXISTS idx_items_status_category;
DROP INDEX IF EXISTS idx_items_status_date;
DROP INDEX IF EXISTS idx_items_category_status_date;

-- Refresh statistics
ANALYZE items;
ANALYZE categories;
ANALYZE speakers;
ANALYZE tags;
ANALYZE item_speakers;
ANALYZE item_tags;
ANALYZE item_embeddings;

-- Show remaining indexes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
