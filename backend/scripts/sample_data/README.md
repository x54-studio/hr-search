# Sample Data

This directory contains sample data for the HR Search system.

## Files

- `speakers.json` - Sample speakers with bios
- `webinars.json` - Sample webinars with metadata, speakers, and tags

## Usage

Run the sample data generator:

```bash
cd C:\Projects\hr-search
python -m backend.scripts.generate_sample
```

## Data Structure

### Speakers
```json
{
  "name": "Speaker Name",
  "bio": "Speaker biography"
}
```

### Webinars
```json
{
  "title": "Webinar Title",
  "description": "Webinar description",
  "category_slug": "category-slug",
  "duration_ms": 2700000,
  "recorded_date": "2024-01-15",
  "speakers": ["Speaker Name"],
  "tags": ["tag1", "tag2"]
}
```

## Notes

- All data is fictional and RODO-compliant
- Speakers must exist before webinars can reference them
- Categories and tags must exist in the database (from seed.sql)
- The script handles conflicts gracefully with ON CONFLICT DO NOTHING
