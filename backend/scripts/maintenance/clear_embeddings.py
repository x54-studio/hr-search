#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Ensure backend is on sys.path
# Handle both running from backend/ and from project root
script_dir = Path(__file__).parent
backend_dir = script_dir.parent.parent  # Go up from scripts/maintenance to backend
sys.path.insert(0, str(backend_dir))

from app.db import get_pool, close_pool


async def main() -> None:
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            await conn.execute('DELETE FROM webinar_embeddings')
            print('✅ Cleared existing embeddings')
    finally:
        await close_pool()
        print('🔌 Database connection closed')


if __name__ == '__main__':
    asyncio.run(main())
