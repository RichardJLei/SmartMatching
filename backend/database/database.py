from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
from .config import get_db_settings
from typing import AsyncGenerator
from fastapi import HTTPException

settings = get_db_settings()
engine = create_async_engine(settings.DB_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    Handles session lifecycle and transaction management.
    
    Yields:
        AsyncSession: Database session for async operations
        
    Raises:
        HTTPException: If database operations fail
    """
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database operation failed: {str(e)}"
        )
    finally:
        await session.close() 