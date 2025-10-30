-- Database Index Simplification Migration
-- Removes over-engineered indexes for portfolio project with ~100 webinars
-- Reduces from 26+ indexes to 10 essential indexes

-- Drop duplicate indexes
DROP INDEX IF EXISTS idx_webinars_title_gin;  -- Duplicate of idx_webinars_title_trgm
DROP INDEX IF EXISTS idx_embeddings_vector_cosine;  -- Duplicate of idx_embeddings_vector

-- Drop unused indexes (never queried)
DROP INDEX IF EXISTS idx_speakers_bio_gin;
DROP INDEX IF EXISTS idx_tags_name_gin;
DROP INDEX IF EXISTS idx_webinars_search_polish;
DROP INDEX IF EXISTS idx_speakers_name_lower;
DROP INDEX IF EXISTS idx_tags_name_lower;

-- Drop over-optimized composite indexes
DROP INDEX IF EXISTS idx_embeddings_type_webinar;
DROP INDEX IF EXISTS idx_webinar_tags_tag_webinar;
DROP INDEX IF EXISTS idx_webinar_speakers_speaker_webinar;
DROP INDEX IF EXISTS idx_webinars_category_date_published;
DROP INDEX IF EXISTS idx_webinars_recorded_published;
DROP INDEX IF EXISTS idx_webinars_status_category;
DROP INDEX IF EXISTS idx_webinars_status_date;
DROP INDEX IF EXISTS idx_webinars_category_status_date;

-- Refresh statistics
ANALYZE webinars;
ANALYZE categories;
ANALYZE speakers;
ANALYZE tags;
ANALYZE webinar_speakers;
ANALYZE webinar_tags;
ANALYZE webinar_embeddings;

-- Show remaining indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
