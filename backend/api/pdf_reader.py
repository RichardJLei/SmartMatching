from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any
from pydantic import BaseModel, UUID4, Field
from utils.pdf_processor import PDFProcessor
from database.database import get_db
from database.models import ConfirmationFile, FileStatusHistory, ProcessingStatus
from enum import Enum
from sqlalchemy import select, update, and_
from datetime import datetime
from services.file_service import FileService
from utils.text_parser import TextParser
from services.model_service import ModelFactory
import logging
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pdf"],
    responses={404: {"description": "Not found"}}
)

class LocationType(str, Enum):
    """Enum for file location types"""
    LOCAL = "local"
    CLOUD = "cloud"

class ModelType(str, Enum):
    """Enum for supported parsing models"""
    DEEPSEEK_CHAT = "deepseek_chat"
    NVIDIA_DEEPSEEK_R1 = "nvidia_deepseek_r1"
    GEMINI = "gemini-2.0-flash"
    # Add more models as needed

class PDFReadRequest(BaseModel):
    """Request model for PDF reading endpoints"""
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

class ParseTextRequest(BaseModel):
    """
    Request model for text parsing endpoint
    
    Attributes:
        file_id: Unique identifier of the file to parse
        model_id: Model to use for parsing, defaults to NVIDIA_DEEPSEEK_R1
    """
    file_id: UUID4
    model_id: ModelType = ModelType.NVIDIA_DEEPSEEK_R1

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

@router.post("/extract-text")
async def extract_text(request: PDFReadRequest):
    """Extract text content from a PDF file."""
    logger.info(f"Starting extract-text for file_id: {request.file_id}")
    
    async with get_db() as db:
        try:
            # Get file with status validation
            file_data = await file_service.get_file_with_status(
                file_id=request.file_id,
                expected_status=[None, ProcessingStatus.Not_Processed]
            )
            
            if request.location == LocationType.LOCAL:
                # Extract text
                result = await pdf_service.extract_text_from_pdf(
                    file_id=request.file_id,
                    file_path=file_data.file_path,
                    file_name=file_data.file_name
                )
                
                if result["data"]["success"]:
                    # Create status history
                    await status_service.create_status_history(
                        file_id=file_data.file_id,
                        previous_status=file_data.processing_status,
                        new_status=ProcessingStatus.TEXT_EXTRACTED,
                        trigger_source="api/extract-text",
                        additional_data={
                            "request_params": {
                                "file_id": str(request.file_id),
                                "location": request.location.value
                            },
                            "extraction_metadata": result["data"].get("metadata", {})
                        }
                    )
                    
                    # Update file status
                    file_data.extracted_text = result["data"]["text_content"]
                    file_data.processing_status = ProcessingStatus.TEXT_EXTRACTED
                    await db.commit()
                    
                    return result
                    
            raise HTTPException(
                status_code=501,
                detail="Cloud storage integration not implemented yet"
            )
                
        except Exception as e:
            await db.rollback()
            logger.error(f"Error in extract_text: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file: {str(e)}"
            )

@router.post("/parse-text")
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
            - model_id (ModelType): AI model to use for parsing:
                - "nvidia_deepseek_r1" (default)
                - "deepseek_chat"
                - "gemini-2.0-flash"
            
    Returns:
        dict: {
            "message": str,  # Success message
            "file_id": str,  # UUID of processed file
            "status": str,   # New processing status ("TEXT_PARSED")
            "parsed_data": {
                "parsed_content": dict,  # Structured data extracted from text
                "model_info": {
                    "provider": str,  # AI model provider (nvidia/openai/gemini)
                    "model": str      # Specific model name used
                }
            }
        }
        
    Status History:
        Records in file_status_history table with:
        - Previous and new status
        - Complete request parameters
        - Full API response
        - Model information
        - Timestamp
        
    Raises:
        HTTPException (400): If file not found or not in TEXT_EXTRACTED status
        HTTPException (500): If parsing or database operations fail
        
    Example:
        ```python
        request = {
            "file_id": "123e4567-e89b-12d3-a456-426614174000",
            "model_id": "nvidia_deepseek_r1"
        }
        ```
    """
    logger.info(f"Starting parse-text for file_id: {request.file_id}")
    
    async with get_db() as db:
        try:
            logger.debug("Acquiring row lock...")
            query = select(ConfirmationFile).where(
                and_(
                    ConfirmationFile.file_id == request.file_id,
                    ConfirmationFile.processing_status == ProcessingStatus.TEXT_EXTRACTED
                )
            ).with_for_update()
            
            logger.debug("Executing database query...")
            result = await db.execute(query)
            file = result.scalar_one_or_none()

            if not file:
                logger.warning(f"File not found or invalid status: {request.file_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File not found or not in TEXT_EXTRACTED status"
                )

            logger.debug(f"Found file: {file.file_id}, status: {file.processing_status}")
            logger.debug("Parsing text with model...")
            
            # Parse text with model and get response
            parsed_data = await TextParser.parse_with_model(
                text=file.extracted_text,
                model_id=request.model_id.value
            )
            logger.debug("Text parsing successful")

            # Prepare response data
            response_data = {
                "message": "Text parsing completed successfully",
                "file_id": str(file.file_id),
                "status": ProcessingStatus.TEXT_PARSED.value,
                "parsed_data": parsed_data
            }

            # Create status history with detailed additional data
            status_history = FileStatusHistory(
                file_id=file.file_id,
                previous_status=ProcessingStatus.TEXT_EXTRACTED,
                new_status=ProcessingStatus.TEXT_PARSED,
                trigger_source="api/parse-text",
                additional_data={
                    "request": {
                        "file_id": str(request.file_id),
                        "model_id": request.model_id.value
                    },
                    "response": response_data,
                    "model_info": parsed_data.get("model_info", {}),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            db.add(status_history)

            # Update file record
            file.parsed_data = parsed_data
            file.processing_status = ProcessingStatus.TEXT_PARSED

            await db.commit()
            return response_data

        except Exception as e:
            logger.error(f"Error in parse_text: {str(e)}", exc_info=True)
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error parsing text: {str(e)}"
            )

@router.get("/test-model-connection")
async def test_model_connection():
    """Test the model API connection"""
    try:
        service = ModelFactory.get_model_service("nvidia_deepseek_r1")
        result = await service.parse_text("Test connection")
        return {"status": "success", "message": "Model connection successful"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model connection test failed: {str(e)}"
        )

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify router configuration"""
    logger.debug("Test endpoint called")
    return {"message": "PDF reader router is working"}

@router.get("/")
async def root():
    """Root endpoint to verify router is mounted"""
    logger.debug("Root endpoint called")
    return {"message": "PDF reader router root endpoint"} 