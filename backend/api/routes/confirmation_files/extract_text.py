from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel, UUID4, Field
import logging
from services.confirmation_files.extract_text_service import ExtractTextService
from database.models import ProcessingStatus
from .types import LocationType  # Import from shared types

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/extract-text",
    tags=["confirmation_files"],
    responses={404: {"description": "Not found"}},
    redirect_slashes=True
)

class ExtractTextRequest(BaseModel):
    """Request model for text extraction endpoints"""
    file_id: UUID4 = Field(
        ...,
        description="Unique identifier of the file to process"
    )
    location: LocationType = Field(
        default=LocationType.LOCAL,
        description="Storage location of the file (local or cloud)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "location": "local"
            }
        }

class ExtractTextResponse(BaseModel):
    """Response model for text extraction"""
    data: Dict[str, Any] = Field(
        ...,
        description="Response data containing extraction results",
        example={
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "completed",
            "success": True,
            "message": "Successfully extracted text from example.pdf",
            "metadata": {
                "page_count": 5,
                "file_size": 1024567,
                "text_length": 15000
            }
        }
    )

@router.post("/", response_model=ExtractTextResponse)
async def extract_text(request: ExtractTextRequest):
    """
    Extract text content from a PDF file.
    
    This endpoint processes a PDF file and extracts its text content.
    Only processes files that are in Not_Processed status.
    
    Args:
        request (ExtractTextRequest): Request containing file_id and location
        
    Returns:
        ExtractTextResponse: Extraction results and metadata
        
    Raises:
        HTTPException (404): If file not found
        HTTPException (400): If file is not in correct status
        HTTPException (500): If extraction fails
    """
    logger.info(f"Starting extract-text for file_id: {request.file_id}")
    
    try:
        service = ExtractTextService()
        result = await service.extract_text(
            file_id=request.file_id,
            location=request.location
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in extract_text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting text: {str(e)}"
        )
