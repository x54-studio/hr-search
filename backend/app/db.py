import asyncpg
import asyncio
from .config import settings

_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        # Retry logic - DB może wstawać wolniej niż API
        for attempt in range(10):
            try:
                _pool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL, 
                    min_size=2, 
                    max_size=10, 
                    command_timeout=10
                )
                break
            except Exception as e:
                if attempt == 9:  # ostatnia próba
                    raise e
                print(f"DB connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None