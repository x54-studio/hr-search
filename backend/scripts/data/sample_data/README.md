# Sample Data

This directory contains sample data for the Search system.

## Files

- `speakers.json` - Sample speakers with bios
- `items.json` - Sample items with metadata, speakers, and tags

## Data Structure

### Speakers
```json
{
  "name": "Speaker Name",
  "bio": "Speaker biography"
}
```

### Items
```json
{
  "title": "Item Title",
  "description": "Item description",
  "category_slug": "category-slug",
  "duration_ms": 2700000,
  "published_date": "2024-01-15",
  "source_type": "webinar",
  "source_url": null,
  "metadata": {},
  "speakers": ["Speaker Name"],
  "tags": ["tag1", "tag2"]
}
```

## Notes

- All data is fictional
- Speakers must exist before items can reference them
- Categories and tags must exist in the database (from seed.sql)
- The script handles conflicts gracefully with ON CONFLICT DO NOTHING
