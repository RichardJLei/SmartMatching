import asyncio
from .database import Base, engine
from fastapi import HTTPException
import logging
from sqlalchemy import text
from .models import ConfirmationFile, ParsingResult  # Import all models explicitly

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def init_db():
    """
    Initialize database with required extensions and tables.
    
    This function:
    1. Creates the pgcrypto extension if not exists
    2. Drops existing tables (warning: destructive operation)
    3. Creates new tables based on SQLAlchemy models
    4. Verifies table creation
    
    Raises:
        HTTPException: If initialization fails
    """
    try:
        async with engine.begin() as conn:
            # Step 1: Create pgcrypto extension
            logger.info("Creating pgcrypto extension...")
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
            
            # Step 2: Drop existing tables
            logger.info("Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            
            # Step 3: Create new tables
            logger.info("Creating new tables...")
            await conn.run_sync(Base.metadata.create_all)
            
            # Step 4: Verify table creation
            tables_to_verify = ['confirmation_files', 'parsing_results']
            for table_name in tables_to_verify:
                result = await conn.execute(
                    text(f"SELECT table_name FROM information_schema.tables WHERE table_name = '{table_name}'")
                )
                if result.scalar():
                    logger.info(f"Table '{table_name}' created successfully")
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Table '{table_name}' was not created"
                    )
                
            logger.info("Database initialization completed successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Database initialization failed: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

def run_init():
    """
    Entry point for database initialization.
    Runs the async initialization function.
    """
    try:
        asyncio.run(init_db())
    except KeyboardInterrupt:
        logger.info("Database initialization interrupted by user")
    except Exception as e:
        logger.error(f"Failed to run database initialization: {str(e)}")
        raise

if __name__ == "__main__":
    run_init() 