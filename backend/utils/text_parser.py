from typing import Dict, Any
from services.model_service import ModelFactory
from fastapi import HTTPException

class TextParser:
    """Handles text parsing operations using different models"""
    
    @staticmethod
    async def parse_with_model(text: str, model_id: str) -> Dict[str, Any]:
        """
        Parse text using specified model
        
        Args:
            text (str): Text to parse
            model_id (str): ID of model to use
            
        Returns:
            Dict[str, Any]: Parsed result including original text
            
        Raises:
            HTTPException: If parsing fails
        """
        try:
            # Get appropriate model service
            model_service = ModelFactory.get_model_service(model_id)
            
            # Parse text using the model
            parsed_result = await model_service.parse_text(text)
            
            return {
                'original_text': text,
                'parsed_result': parsed_result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Text parsing failed: {str(e)}"
            ) 