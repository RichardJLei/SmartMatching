from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator
from enum import Enum
import logging
from config.model_config import get_model_settings
from fastapi import HTTPException
import json
import os
from pathlib import Path
import re

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
            
        try:
            settings = get_model_settings()
            logger.info(f"Loaded model settings. Base URL: {settings.NVIDIA_BASE_URL}")
            
            if not settings.NVIDIA_API_KEY:
                raise ValueError("NVIDIA_API_KEY is empty")
                
            self.client = OpenAI(
                base_url=settings.NVIDIA_BASE_URL,
                api_key=settings.NVIDIA_API_KEY
            )
            self.model_name = settings.NVIDIA_MODEL_NAME
            
            # Load parsing instructions
            self.instructions = self._load_instructions()
            
        except Exception as e:
            logger.error(f"Failed to initialize NvidiaDeepseekService: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize model service: {str(e)}"
            )
    
    def _load_instructions(self) -> str:
        """
        Load parsing instructions from rules file
        
        Returns:
            str: Instructions content
            
        Raises:
            HTTPException: If file cannot be loaded
        """
        try:
            # Get the absolute path to the rules file
            base_path = Path(__file__).parent.parent  # Go up two levels from services to backend
            rules_path = base_path / "utils" / "ConvertBankingConfoInstruction.rules"
            
            logger.info(f"Loading rules from: {rules_path}")
            
            if not rules_path.exists():
                raise FileNotFoundError(f"Rules file not found at: {rules_path}")
                
            with open(rules_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            if not content:
                raise ValueError("Rules file is empty")
                
            return content
            
        except Exception as e:
            logger.error(f"Failed to load parsing instructions: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load parsing instructions: {str(e)}"
            )
    
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
            logger.info("Starting text parsing with Nvidia model")
            
            # Log input text length
            logger.info(f"Input text length: {len(text)}")
            
            # Construct prompt with instructions and text
            prompt = f"""
            Please follow these instructions to extract JSON from the FX Confirmation Letter:

            {self.instructions}

            Here's the text to parse:
            {text}

            Please extract the information and return it in valid JSON format following the specified structure.
            Only return the JSON object, no additional text.
            """
            
            logger.info("Making API request to Nvidia model")
            logger.info(f"Using model: {self.model_name}")
            logger.info(f"Base URL: {self.client.base_url}")
            
            # First test API connection with a simple request
            try:
                test_messages = [{"role": "user", "content": "Test connection"}]
                test_completion = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=test_messages,
                    max_tokens=10,
                    stream=False
                )
                logger.info("API connection test successful")
            except Exception as e:
                logger.error(f"API connection test failed: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to connect to Nvidia API: {str(e)}"
                )

            # If connection test passes, proceed with actual request
            logger.info("Sending main request to model")
            messages = [{"role": "user", "content": prompt}]
            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
                top_p=0.7,
                max_tokens=4096,
                stream=True
            )
            
            # Process streaming response
            logger.info("Processing streaming response")
            full_response = ""
            async for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    logger.debug(f"Received chunk: {chunk.choices[0].delta.content}")
            
            logger.info(f"Full response length: {len(full_response)}")
            
            # Parse the response as JSON
            try:
                logger.info("Parsing response as JSON")
                parsed_json = json.loads(full_response)
                result = {
                    "parsed_content": parsed_json,
                    "model_info": {
                        "provider": ModelProvider.NVIDIA.value,
                        "model": self.model_name
                    }
                }
                logger.info("Successfully parsed response")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse model response as JSON: {str(e)}")
                logger.error(f"Raw response: {full_response}")
                raise HTTPException(
                    status_code=500,
                    detail="Model response was not valid JSON"
                )
            
        except Exception as e:
            logger.error(f"Nvidia model parsing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Model parsing failed: {str(e)}"
            )

class DeepSeekChatService(BaseModelService):
    """Implementation for DeepSeek Chat model"""
    
    def __init__(self):
        """Initialize DeepSeek model client"""
        if not OPENAI_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="OpenAI package not installed. Please install with 'pip install openai'"
            )
            
        try:
            settings = get_model_settings()
            logger.info(f"Loaded model settings for DeepSeek")
            
            if not settings.DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY is empty")
                
            self.client = OpenAI(
                base_url=settings.DEEPSEEK_BASE_URL,
                api_key=settings.DEEPSEEK_API_KEY
            )
            self.model_name = settings.DEEPSEEK_MODEL_NAME
            
            # Load parsing instructions
            self.instructions = self._load_instructions()
            
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeekChatService: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize model service: {str(e)}"
            )
    
    def _load_instructions(self) -> str:
        """Load parsing instructions from rules file"""
        try:
            base_path = Path(__file__).parent.parent
            rules_path = base_path / "utils" / "ConvertBankingConfoInstruction.rules"
            
            logger.info(f"Loading rules from: {rules_path}")
            
            if not rules_path.exists():
                raise FileNotFoundError(f"Rules file not found at: {rules_path}")
                
            with open(rules_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            if not content:
                raise ValueError("Rules file is empty")
                
            return content
            
        except Exception as e:
            logger.error(f"Failed to load parsing instructions: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load parsing instructions: {str(e)}"
            )
    
    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from response that might be wrapped in markdown code blocks
        
        Args:
            response (str): Raw response from model
            
        Returns:
            str: Cleaned JSON string
            
        Raises:
            ValueError: If no JSON found in response
        """
        # Try to find JSON between ```json and ``` markers
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no markdown blocks found, return the original response
        return response.strip()

    async def parse_text(self, text: str) -> Dict[str, Any]:
        """Parse text using DeepSeek Chat model"""
        try:
            logger.info("Starting text parsing with DeepSeek model")
            logger.info(f"Input text length: {len(text)}")
            
            system_prompt = f"""You are a financial document parser. 
            Follow these instructions to extract information:
            
            {self.instructions}
            
            Important: Return only the JSON object without any markdown formatting or additional text."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
            
            logger.info("Making API request to DeepSeek model")
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
                stream=True
            )
            
            logger.info("Processing streaming response")
            full_response = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    logger.debug(f"Received chunk: {chunk.choices[0].delta.content}")
            
            logger.info(f"Full response length: {len(full_response)}")
            logger.debug(f"Raw response: {full_response}")
            
            try:
                # Clean the response before parsing
                cleaned_json_str = self._extract_json_from_response(full_response)
                logger.debug(f"Cleaned JSON string: {cleaned_json_str}")
                
                logger.info("Parsing response as JSON")
                parsed_json = json.loads(cleaned_json_str)
                result = {
                    "parsed_content": parsed_json,
                    "model_info": {
                        "provider": ModelProvider.OPENAI.value,
                        "model": self.model_name
                    }
                }
                logger.info("Successfully parsed response")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse model response as JSON: {str(e)}")
                logger.error(f"Raw response: {full_response}")
                raise HTTPException(
                    status_code=500,
                    detail="Model response was not valid JSON"
                )
            
        except Exception as e:
            logger.error(f"DeepSeek model parsing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Model parsing failed: {str(e)}"
            )

class ModelFactory:
    """Factory for creating model service instances"""
    
    @staticmethod
    def get_model_service(model_type: str) -> BaseModelService:
        """Get appropriate model service based on model type"""
        if model_type == "nvidia_deepseek_r1":
            return NvidiaDeepseekService()
        elif model_type == "deepseek_chat":
            return DeepSeekChatService()
            
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model type: {model_type}"
        ) 