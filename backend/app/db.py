import asyncpg
import asyncio
import logging
from .config import settings

_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        # Retry logic - DB może wstawać wolniej niż API
        logger = logging.getLogger("hr_search.db")
        for attempt in range(10):
            try:
                _pool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL, 
                    min_size=2, 
                    max_size=10, 
                    command_timeout=10
                )
                logger.info("Database pool created")
                break
            except Exception as e:
                if attempt == 9:  # ostatnia próba
                    raise e
                logger.warning("DB connection attempt failed", extra={
                    "attempt": attempt + 1,
                    "error": str(e)
                })
                await asyncio.sleep(0.3)
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        logging.getLogger("hr_search.db").info("Database pool closed")
        _pool = None