from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel, UUID4
from utils.pdf_processor import PDFProcessor
from database.database import get_db
from database.models import ConfirmationFile
from enum import Enum
from sqlalchemy import select, update
from datetime import datetime
from services.file_service import FileService
from utils.text_parser import TextParser
from services.model_service import ModelFactory
import logging

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
    # Add more models as needed

class PDFReadRequest(BaseModel):
    """Request model for PDF reading endpoints"""
    file_id: UUID4
    location: LocationType = LocationType.LOCAL  # Default to local

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

@router.post("/extract-text")
async def extract_text(request: PDFReadRequest):
    """
    Extract text content from a PDF file.
    
    Args:
        request (PDFReadRequest): Request containing file_id and location
        
    Returns:
        dict: Contains extracted text and metadata
    """
    logger.debug(f"Received extract-text request with file_id: {request.file_id}")
    logger.debug(f"Location type: {request.location}")
    
    async with get_db() as db:
        # Query using SQLAlchemy ORM
        query = select(ConfirmationFile).where(ConfirmationFile.file_id == request.file_id)
        logger.debug(f"Executing database query: {query}")
        result = await db.execute(query)
        file_data = result.scalar_one_or_none()
        
        logger.debug(f"Database query result: {file_data}")
        
        if not file_data:
            logger.error(f"File not found with ID: {request.file_id}")
            raise HTTPException(
                status_code=404,
                detail=f"File with ID {request.file_id} not found"
            )
        
        # Check if text has already been extracted
        if file_data.processing_status == 'extracted':
            return {
                "data": {
                    "id": str(request.file_id),
                    "status": "completed",
                    "success": True,
                    "message": "Text already extracted",
                    "metadata": {
                        "processing_status": file_data.processing_status,
                        "extracted_text_length": len(file_data.extracted_text or "")
                    }
                }
            }
        
        try:
            # Update status to processing
            file_data.processing_status = 'processing'
            await db.commit()
            
            if request.location == LocationType.LOCAL:
                if not file_data.file_path:
                    raise HTTPException(
                        status_code=400,
                        detail="File path not found in database"
                    )
                
                # Extract text using PDFProcessor
                result = await PDFProcessor.extract_text_from_pdf(
                    file_id=request.file_id,
                    file_path=file_data.file_path,
                    file_name=file_data.file_name
                )
                
                if result["data"]["success"]:
                    # Update processing status to extracted
                    file_data.processing_status = 'extracted'
                    await db.commit()
                else:
                    # Update status to error if extraction failed
                    file_data.processing_status = 'error'
                    await db.commit()
                
                return result
                
            else:
                # Update status to error for unsupported location
                file_data.processing_status = 'error'
                await db.commit()
                raise HTTPException(
                    status_code=501,
                    detail="Cloud storage integration not implemented yet"
                )
                
        except Exception as e:
            # Update status to error on exception
            file_data.processing_status = 'error'
            await db.commit()
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file: {str(e)}"
            )

@router.post("/parse-text")
async def parse_text(request: ParseTextRequest):
    """
    Parse extracted text using specified model.
    
    Args:
        request (ParseTextRequest): Contains file_id and model selection
        
    Returns:
        dict: Contains parsing results and status following Refine patterns
        
    Raises:
        HTTPException: If parsing fails or file not found
    """
    # Get file data and validate
    file_data = await FileService.get_extracted_file(request.file_id)
    
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    if file_data.processing_status != 'extracted':
        raise HTTPException(status_code=400, detail="File text not yet extracted")
    if not file_data.extracted_text:
        raise HTTPException(status_code=404, detail="No extracted text found")

    try:
        # Get parsed result using specified model
        result = await TextParser.parse_with_model(
            file_data.extracted_text,
            request.model_id.value
        )
        
        # Log only essential information
        logger.info(f"Received parsing result for file_id: {request.file_id}")
        
        # Ensure result has the expected structure
        if not isinstance(result, dict):
            raise ValueError(f"Expected dict result, got {type(result)}")
            
        # Get parsed_content with fallback
        parsed_content = result.get('parsed_content', result)
        model_info = result.get('model_info', {
            'provider': 'unknown', 
            'model': request.model_id.value
        })

        # Create database-ready parsed result
        db_parsed_result = {
            "content": parsed_content,
            "model": {
                "id": request.model_id.value,
                "info": model_info
            },
            "metadata": {
                "processing_timestamp": datetime.utcnow().isoformat(),
                "original_text_length": len(file_data.extracted_text)
            }
        }

        # Update database with parsed result and handle versioning
        parsing_result = await FileService.create_parsing_result(
            file_id=request.file_id,
            parsed_data=db_parsed_result,
            model_id=request.model_id.value
        )

        # Return successful response
        return {
            "data": {
                "id": str(request.file_id),
                "parsing_result_id": str(parsing_result.parsing_result_id),
                "status": "completed",
                "success": True,
                "model": {
                    "id": request.model_id.value,
                    "info": model_info
                },
                "result": parsed_content,
                "metadata": {
                    "version": parsing_result.version,
                    "is_latest": parsing_result.latest,
                    "original_text_length": len(file_data.extracted_text),
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
            }
        }

    except Exception as e:
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error in parse_text: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Parsing failed: {str(e)}"
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