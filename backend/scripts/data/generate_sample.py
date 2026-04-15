#!/usr/bin/env python3
"""
Generate sample data for the Search system.
Loads speakers and items from JSON files and inserts them into database.
"""
import asyncio
import json
import uuid
from pathlib import Path
import sys
from datetime import date

# Add backend to path so we can import modules
script_dir = Path(__file__).parent
backend_dir = script_dir.parent.parent
sys.path.insert(0, str(backend_dir))

from app.dependencies import DatabaseManager

async def load_sample_data():
    """Load sample data from JSON files into database."""
    print("Starting sample data generation...")

    pool = None
    try:
        db_manager = DatabaseManager()
        pool = await db_manager.create_pool()
        print("Connected to database")

        data_dir = Path(__file__).parent / "sample_data"

        with open(data_dir / "speakers.json", encoding="utf-8") as f:
            speakers = json.load(f)
        print(f"Loaded {len(speakers)} speakers")

        with open(data_dir / "items.json", encoding="utf-8") as f:
            items = json.load(f)
        print(f"Loaded {len(items)} items")

        async with pool.acquire() as conn:
            existing = await conn.fetchval("SELECT COUNT(*) FROM items")
            if existing > 0:
                print(f"Database already has {existing} items, skipping. Use docker compose down -v to reset.")
                return

            print("Inserting speakers...")
            for speaker in speakers:
                await conn.execute("""
                    INSERT INTO speakers (id, name, bio)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (name) DO UPDATE SET bio = $3
                """, uuid.uuid4(), speaker["name"], speaker["bio"])
            print(f"Inserted {len(speakers)} speakers")

            print("Inserting items...")
            inserted_items = 0
            for item in items:
                category_id = await conn.fetchval(
                    "SELECT id FROM categories WHERE slug = $1",
                    item["category_slug"]
                )

                if not category_id:
                    print(f"Warning: Category '{item['category_slug']}' not found, skipping item '{item['title']}'")
                    continue

                published_date = date.fromisoformat(item["published_date"])
                source_type = item.get("source_type", "webinar")
                source_url = item.get("source_url")
                metadata = json.dumps(item.get("metadata", {}))

                item_id = await conn.fetchval("""
                    INSERT INTO items (id, title, description, category_id, duration_ms, published_date, source_type, source_url, metadata, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, 'published')
                    RETURNING id
                """, uuid.uuid4(), item["title"], item["description"],
                     category_id, item["duration_ms"], published_date,
                     source_type, source_url, metadata)

                for speaker_name in item["speakers"]:
                    speaker_id = await conn.fetchval(
                        "SELECT id FROM speakers WHERE name = $1", speaker_name
                    )
                    if speaker_id:
                        await conn.execute("""
                            INSERT INTO item_speakers (item_id, speaker_id)
                            VALUES ($1, $2) ON CONFLICT DO NOTHING
                        """, item_id, speaker_id)
                    else:
                        print(f"Warning: Speaker '{speaker_name}' not found for item '{item['title']}'")

                for tag_name in item["tags"]:
                    tag_id = await conn.fetchval(
                        "SELECT id FROM tags WHERE name = $1", tag_name
                    )
                    if tag_id:
                        await conn.execute("""
                            INSERT INTO item_tags (item_id, tag_id)
                            VALUES ($1, $2) ON CONFLICT DO NOTHING
                        """, item_id, tag_id)
                    else:
                        print(f"Warning: Tag '{tag_name}' not found for item '{item['title']}'")

                inserted_items += 1

            print(f"Inserted {inserted_items} items")

            total_items = await conn.fetchval("SELECT COUNT(*) FROM items WHERE status = 'published'")
            total_speakers = await conn.fetchval("SELECT COUNT(*) FROM speakers")
            total_tags = await conn.fetchval("SELECT COUNT(*) FROM tags")

            print(f"\nDatabase summary:")
            print(f"   Items: {total_items}")
            print(f"   Speakers: {total_speakers}")
            print(f"   Tags: {total_tags}")

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        if pool:
            await pool.close()

if __name__ == "__main__":
    asyncio.run(load_sample_data())
