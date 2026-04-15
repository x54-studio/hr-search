#!/usr/bin/env python3
"""Generate embeddings for all items using service layer."""
import asyncio
import sys
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.dependencies import DatabaseManager, ModelManager, get_embedding_service, get_embedding_repository
from app.logging_config import setup_logging, get_logger

logger = get_logger("generate_embeddings")

async def main():
    """Generate embeddings for all items."""
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting embedding generation...")
    
    pool = None
    model_manager = None
    
    try:
        # Initialize database
        db_manager = DatabaseManager()
        pool = await db_manager.create_pool()
        logger.info("Database pool created")
        
        # Initialize model
        model_manager = ModelManager()
        await model_manager.initialize_model()
        logger.info("Model initialized")
        
        # Create service
        embedding_repo = get_embedding_repository(pool)
        
        # Create a simple app-like object for DI
        class AppState:
            pass
        app = AppState()
        app.state = AppState()
        app.state.model_manager = model_manager
        
        embedding_service = get_embedding_service(embedding_repo, app)
        
        # Generate embeddings
        await embedding_service.generate_all_embeddings()
        
        logger.info("Embedding generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
    finally:
        if model_manager:
            await model_manager.cleanup_model()
        if pool:
            await pool.close()
        logger.info("Cleanup completed")

if __name__ == "__main__":
    asyncio.run(main())