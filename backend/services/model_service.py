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
from tenacity import retry, stop_after_attempt, wait_exponential

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
    
    def __init__(self):
        """Initialize base model service"""
        if not OPENAI_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="OpenAI package not installed. Please install with 'pip install openai'"
            )
        self.settings = get_model_settings()
        self.instructions = self._load_instructions()
    
    def _load_instructions(self) -> str:
        """Load parsing instructions from rules file"""
        try:
            base_path = Path(__file__).parent.parent
            rules_path = base_path / "utils" / "ConvertBankingConfoInstruction.rules"
            logger.info(f"Loading rules from: {rules_path}")
            
            with open(rules_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"Failed to load instructions: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to load parsing instructions"
            )
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from response that might be wrapped in markdown"""
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        return matches[0].strip() if matches else response.strip()
    
    async def _process_streaming_response(self, completion) -> str:
        """Process streaming response from model"""
        full_response = ""
        async for chunk in completion:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response
    
    def _create_result(self, parsed_json: Dict, provider: ModelProvider) -> Dict:
        """Create standardized result dictionary"""
        return {
            "parsed_content": parsed_json,
            "model_info": {
                "provider": provider.value,
                "model": self.model_name
            }
        }

class NvidiaDeepseekService(BaseModelService):
    """Implementation for Nvidia's Deepseek model"""
    
    def __init__(self):
        """Initialize Nvidia model client"""
        super().__init__()
        self.client = OpenAI(
            base_url=self.settings.NVIDIA_BASE_URL,
            api_key=self.settings.NVIDIA_API_KEY
        )
        self.model_name = self.settings.NVIDIA_MODEL_NAME

    async def parse_text(self, text: str) -> Dict[str, Any]:
        """Parse text using Nvidia's Deepseek model"""
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
            
            full_response = await self._process_streaming_response(completion)
            cleaned_json = self._extract_json_from_response(full_response)
            parsed_json = json.loads(cleaned_json)
            
            return self._create_result(parsed_json, ModelProvider.NVIDIA)
            
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
        super().__init__()
        self.client = OpenAI(
            base_url=self.settings.DEEPSEEK_BASE_URL,
            api_key=self.settings.DEEPSEEK_API_KEY
        )
        self.model_name = self.settings.DEEPSEEK_MODEL_NAME

    def _validate_request(self, text: str) -> None:
        """Validate the request parameters"""
        if not text or not isinstance(text, str):
            raise HTTPException(
                status_code=400,
                detail="Invalid input: text must be a non-empty string"
            )
        
        if len(text.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid input: text cannot be empty or whitespace only"
            )

    async def _make_model_request(self, messages: list) -> str:
        """Make request to the model"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
                stream=False
            )
            
            if not completion or not completion.choices:
                raise ValueError("Empty response from model")
                
            response_content = completion.choices[0].message.content
            if not response_content:
                raise ValueError("Empty content in model response")
                
            return response_content
            
        except Exception as e:
            logger.error(f"Model request failed: {str(e)}")
            raise

    async def parse_text(self, text: str) -> Dict[str, Any]:
        """Parse text using DeepSeek Chat model"""
        try:
            # Validate input
            self._validate_request(text)
            
            logger.info("Starting text parsing with model")
            
            # Prepare messages
            system_prompt = f"""
            Please return the response in valid JSON format.
            {self.instructions}
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
            
            # Make request without retry
            response_content = await self._make_model_request(messages)
            
            # Try parsing the raw response
            try:
                return self._create_result(json.loads(response_content), ModelProvider.OPENAI)
            except json.JSONDecodeError:
                # If parsing fails, try to clean and repair the JSON
                cleaned_json = self._clean_and_repair_json(response_content)
                return self._create_result(cleaned_json, ModelProvider.OPENAI)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Model parsing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Model parsing failed: {str(e)}"
            )

    def _clean_and_repair_json(self, response_content: str) -> Dict:
        """Clean and repair JSON response"""
        try:
            # Basic cleaning
            cleaned_response = response_content.strip().replace('\n', '').replace('\t', '')
            
            # Extract JSON structure
            try:
                start_index = cleaned_response.index('{')
                end_index = cleaned_response.rindex('}') + 1
                extracted_json = cleaned_response[start_index:end_index]
            except ValueError:
                raise ValueError("Could not find valid JSON structure in response")
            
            # Remove any non-JSON characters
            extracted_json = re.sub(r'^[^\{]*', '', extracted_json)
            extracted_json = re.sub(r'[^\}]*$', '', extracted_json)
            
            # Fix common JSON issues
            fixed_json = extracted_json.replace("'", '"')
            fixed_json = re.sub(r',\s*}', '}', fixed_json)
            fixed_json = re.sub(r',\s*]', ']', fixed_json)
            
            return json.loads(fixed_json)
            
        except Exception as e:
            logger.error(f"JSON cleaning failed: {str(e)}")
            raise ValueError(f"Failed to clean and repair JSON: {str(e)}")

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