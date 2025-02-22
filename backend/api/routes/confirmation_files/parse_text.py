from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel, UUID4, Field
from enum import Enum
import logging
from services.confirmation_files.parse_text_service import ParseTextService

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/parse-text",
    tags=["confirmation_files"],
    responses={404: {"description": "Not found"}},
    redirect_slashes=True
)

class ModelType(str, Enum):
    """Enum for supported parsing models"""
    DEEPSEEK_CHAT = "deepseek_chat"
    NVIDIA_DEEPSEEK_R1 = "nvidia_deepseek_r1"
    GEMINI = "gemini-2.0-flash"

class ParseTextRequest(BaseModel):
    """
    Request model for text parsing endpoint
    
    Attributes:
        file_id: Unique identifier of the file to parse
        model_id: Model to use for parsing, defaults to NVIDIA_DEEPSEEK_R1
    """
    file_id: UUID4
    model_id: ModelType = ModelType.NVIDIA_DEEPSEEK_R1

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "model_id": "nvidia_deepseek_r1"
            }
        }

class ParseTextResponse(BaseModel):
    """Response model for text parsing"""
    data: Dict[str, Any] = Field(
        ...,
        description="Response data containing parsing results",
        example={
            "message": "Text parsing completed successfully",
            "file_id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "TEXT_PARSED",
            "parsed_data": {
                "parsed_content": {},
                "model_info": {
                    "provider": "nvidia",
                    "model": "nvidia_deepseek_r1"
                }
            }
        }
    )

@router.post("/", response_model=ParseTextResponse)
async def parse_text(request: ParseTextRequest):
    """
    Parse extracted text from a confirmation file using AI models.
    
    This endpoint:
    1. Validates the file exists and is in TEXT_EXTRACTED status
    2. Uses specified AI model to parse the extracted text
    3. Updates the file status to TEXT_PARSED
    4. Records detailed status change history
    
    Args:
        request (ParseTextRequest): Request containing:
            - file_id (UUID): ID of file to parse
            - model_id (ModelType): AI model to use for parsing
            
    Returns:
        ParseTextResponse: Parsing results and metadata
        
    Raises:
        HTTPException (400): If file not found or not in TEXT_EXTRACTED status
        HTTPException (500): If parsing or database operations fail
    """
    logger.info(f"Starting parse-text for file_id: {request.file_id}")
    
    try:
        service = ParseTextService()
        result = await service.parse_text(
            file_id=request.file_id,
            model_id=request.model_id.value
        )
        return ParseTextResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in parse_text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing text: {str(e)}"
        )
