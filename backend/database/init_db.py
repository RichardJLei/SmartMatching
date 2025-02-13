import asyncio
from .database import Base, engine
from fastapi import HTTPException
import logging
from sqlalchemy import text
from .models import ConfirmationFile  # Import the model explicitly

logger = logging.getLogger(__name__)
# Set logging level to see more details
logging.basicConfig(level=logging.INFO)

async def init_db():
    """Initialize database with required extensions and tables"""
    try:
        async with engine.begin() as conn:
            # Create pgcrypto extension using text()
            logger.info("Creating pgcrypto extension...")
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
            
            # Create tables
            logger.info("Creating tables...")
            # Import the model to ensure it's registered with Base
            await conn.run_sync(Base.metadata.drop_all)  # Drop existing tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Verify table creation
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'confirmation_files'"))
            if result.scalar():
                logger.info("Table 'confirmation_files' created successfully")
            else:
                logger.error("Table 'confirmation_files' was not created")
                
            logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(init_db()) 