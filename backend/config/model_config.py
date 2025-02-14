from pydantic_settings import BaseSettings
from functools import lru_cache

class ModelSettings(BaseSettings):
    """
    Model configuration settings.
    Loads from environment variables or .env file.
    """
    NVIDIA_API_KEY: str
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL_NAME: str = "deepseek-ai/deepseek-r1"

    class Config:
        env_file = "backend/config/.env"

@lru_cache()
def get_model_settings() -> ModelSettings:
    """
    Get cached model settings.
    
    Returns:
        ModelSettings: Model configuration
    """
    return ModelSettings() 