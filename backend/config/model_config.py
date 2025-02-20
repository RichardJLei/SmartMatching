from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path
from fastapi import HTTPException

class ModelSettings(BaseSettings):
    """
    Model configuration settings.
    Loads from environment variables or .env file.
    """
    # Nvidia settings
    NVIDIA_API_KEY: str
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL_NAME: str = "deepseek-ai/deepseek-r1"
    
    # DeepSeek-chat settings
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"

    # Gemini settings
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash"

    class Config:
        # Get the absolute path to the .env file
        env_file = str(Path(__file__).parent / ".env")
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in .env file

@lru_cache()
def get_model_settings() -> ModelSettings:
    """
    Get cached model settings.
    
    Returns:
        ModelSettings: Model configuration
        
    Raises:
        HTTPException: If configuration is invalid
    """
    try:
        settings = ModelSettings()
        # Add validation logging
        if not settings.NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY is missing or empty")
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model settings: {str(e)}"
        ) 