from pydantic_settings import BaseSettings
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    DB_URL: str

    class Config:
        env_file = "config/.env"
        # Only allow DB_URL from env file
        extra = "ignore"  # Ignore extra fields from env file

@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Get database settings with caching"""
    return DatabaseSettings() 