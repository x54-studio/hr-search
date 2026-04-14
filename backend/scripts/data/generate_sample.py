#!/usr/bin/env python3
"""
Generate sample data for HR Search system.
Loads speakers and webinars from JSON files and inserts them into database.
"""
import asyncio
import json
import uuid
from pathlib import Path
import sys
import os
from datetime import date

# Add backend to path so we can import modules
# Handle both running from backend/ and from project root
script_dir = Path(__file__).parent
backend_dir = script_dir.parent.parent  # Go up from scripts/data to backend
sys.path.insert(0, str(backend_dir))

from app.dependencies import DatabaseManager

async def load_sample_data():
    """Load sample data from JSON files into database."""
    print("🚀 Starting sample data generation...")

    pool = None
    try:
        db_manager = DatabaseManager()
        pool = await db_manager.create_pool()
        print("✅ Connected to database")
        
        # Load JSON files
        data_dir = Path(__file__).parent / "sample_data"
        
        # Load speakers
        with open(data_dir / "speakers.json", encoding="utf-8") as f:
            speakers = json.load(f)
        print(f"📄 Loaded {len(speakers)} speakers")
        
        # Load webinars
        with open(data_dir / "webinars.json", encoding="utf-8") as f:
            webinars = json.load(f)
        print(f"📄 Loaded {len(webinars)} webinars")
        
        async with pool.acquire() as conn:
            # Check if webinars already exist
            existing = await conn.fetchval("SELECT COUNT(*) FROM webinars")
            if existing > 0:
                print(f"⚠️  Database already has {existing} webinars, skipping. Use docker compose down -v to reset.")
                return

            # Insert speakers
            print("👥 Inserting speakers...")
            for speaker in speakers:
                await conn.execute("""
                    INSERT INTO speakers (id, name, bio) 
                    VALUES ($1, $2, $3)
                    ON CONFLICT (name) DO UPDATE SET bio = $3
                """, uuid.uuid4(), speaker["name"], speaker["bio"])
            print(f"✅ Inserted {len(speakers)} speakers")
            
            # Insert webinars
            print("🎥 Inserting webinars...")
            inserted_webinars = 0
            for webinar in webinars:
                # Get category_id
                category_id = await conn.fetchval(
                    "SELECT id FROM categories WHERE slug = $1", 
                    webinar["category_slug"]
                )
                
                if not category_id:
                    print(f"⚠️  Warning: Category '{webinar['category_slug']}' not found, skipping webinar '{webinar['title']}'")
                    continue
                
                # Convert date string to date object
                recorded_date = date.fromisoformat(webinar["recorded_date"])
                
                # Insert webinar
                webinar_id = await conn.fetchval("""
                    INSERT INTO webinars (id, title, description, category_id, duration_ms, recorded_date, status)
                    VALUES ($1, $2, $3, $4, $5, $6, 'published')
                    RETURNING id
                """, uuid.uuid4(), webinar["title"], webinar["description"], 
                     category_id, webinar["duration_ms"], recorded_date)
                
                # Link speakers
                for speaker_name in webinar["speakers"]:
                    speaker_id = await conn.fetchval(
                        "SELECT id FROM speakers WHERE name = $1", speaker_name
                    )
                    if speaker_id:
                        await conn.execute("""
                            INSERT INTO webinar_speakers (webinar_id, speaker_id)
                            VALUES ($1, $2) ON CONFLICT DO NOTHING
                        """, webinar_id, speaker_id)
                    else:
                        print(f"⚠️  Warning: Speaker '{speaker_name}' not found for webinar '{webinar['title']}'")
                
                # Link tags
                for tag_name in webinar["tags"]:
                    tag_id = await conn.fetchval(
                        "SELECT id FROM tags WHERE name = $1", tag_name
                    )
                    if tag_id:
                        await conn.execute("""
                            INSERT INTO webinar_tags (webinar_id, tag_id)
                            VALUES ($1, $2) ON CONFLICT DO NOTHING
                        """, webinar_id, tag_id)
                    else:
                        print(f"⚠️  Warning: Tag '{tag_name}' not found for webinar '{webinar['title']}'")
                
                inserted_webinars += 1
            
            print(f"✅ Inserted {inserted_webinars} webinars")
            
            # Show summary
            total_webinars = await conn.fetchval("SELECT COUNT(*) FROM webinars WHERE status = 'published'")
            total_speakers = await conn.fetchval("SELECT COUNT(*) FROM speakers")
            total_tags = await conn.fetchval("SELECT COUNT(*) FROM tags")
            
            print("\n📊 Database summary:")
            print(f"   Webinars: {total_webinars}")
            print(f"   Speakers: {total_speakers}")
            print(f"   Tags: {total_tags}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        if pool:
            await pool.close()
        print("🔌 Database connection cleanup completed")

if __name__ == "__main__":
    asyncio.run(load_sample_data())
