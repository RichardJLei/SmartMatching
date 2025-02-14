from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator
from enum import Enum
import logging
from config.model_config import get_model_settings
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)

# Try importing OpenAI, handle if not installed
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not installed. Some features may not be available.")
    OPENAI_AVAILABLE = False

class ModelProvider(str, Enum):
    """Supported AI model providers"""
    NVIDIA = "nvidia"
    OPENAI = "openai"
    # Add more providers as needed

class BaseModelService(ABC):
    """Abstract base class for AI model services"""
    
    @abstractmethod
    async def parse_text(self, text: str) -> Dict[str, Any]:
        """
        Parse text using the AI model
        
        Args:
            text (str): Text to parse
            
        Returns:
            Dict[str, Any]: Parsed result
            
        Raises:
            HTTPException: If parsing fails
        """
        pass

class NvidiaDeepseekService(BaseModelService):
    """Implementation for Nvidia's Deepseek model"""
    
    def __init__(self):
        """Initialize Nvidia model client"""
        if not OPENAI_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="OpenAI package not installed. Please install with 'pip install openai'"
            )
            
        settings = get_model_settings()
        self.client = OpenAI(
            base_url=settings.NVIDIA_BASE_URL,
            api_key=settings.NVIDIA_API_KEY
        )
        self.model_name = settings.NVIDIA_MODEL_NAME
    
    async def parse_text(self, text: str) -> Dict[str, Any]:
        """
        Parse text using Nvidia's Deepseek model
        
        Args:
            text (str): Text to parse
            
        Returns:
            Dict[str, Any]: Parsed result
            
        Raises:
            HTTPException: If parsing fails
        """
        try:
            messages = [{"role": "user", "content": text}]
            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.6,
                top_p=0.7,
                max_tokens=4096,
                stream=True
            )
            
            # Process streaming response
            full_response = ""
            async for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
            
            # TODO: Process the response into structured format
            return {
                "parsed_content": full_response,
                "model_info": {
                    "provider": ModelProvider.NVIDIA.value,
                    "model": self.model_name
                }
            }
            
        except Exception as e:
            logger.error(f"Nvidia model parsing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Model parsing failed: {str(e)}"
            )

class ModelFactory:
    """Factory for creating model service instances"""
    
    @staticmethod
    def get_model_service(model_type: str) -> BaseModelService:
        """
        Get appropriate model service based on model type
        
        Args:
            model_type (str): Type of model to use
            
        Returns:
            BaseModelService: Model service instance
            
        Raises:
            HTTPException: If model type is not supported
        """
        if model_type == "nvidia_deepseek_r1":
            return NvidiaDeepseekService()
        # Add more model services here
        
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model type: {model_type}"
        ) 