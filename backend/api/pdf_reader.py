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
    prefix="/api",
    tags=["api"],
    responses={404: {"description": "Not found"}},
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
    location: LocationType

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
    async with get_db() as db:
        # Query using SQLAlchemy ORM
        query = select(ConfirmationFile).where(ConfirmationFile.file_id == request.file_id)
        result = await db.execute(query)
        file_data = result.scalar_one_or_none()
        
        if not file_data:
            raise HTTPException(
                status_code=404,
                detail=f"File with ID {request.file_id} not found"
            )
        
        if request.location == LocationType.LOCAL:
            if not file_data.file_path:
                raise HTTPException(
                    status_code=400,
                    detail="File path not found in database"
                )
            return await PDFProcessor.extract_text_from_pdf(
                file_id=request.file_id,
                file_path=file_data.file_path,
                file_name=file_data.file_name
            )
        else:
            # TODO: Implement cloud storage retrieval
            raise HTTPException(
                status_code=501,
                detail="Cloud storage integration not implemented yet"
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
        HTTPException: If file not found or processing fails
    """
    try:
        file_data = await FileService.get_extracted_file(request.file_id)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        if file_data.processing_status != 'extracted':
            raise HTTPException(status_code=400, detail="File text not yet extracted")
        if not file_data.extracted_text:
            raise HTTPException(status_code=404, detail="No extracted text found")

        # Get parsed result using specified model
        result = await TextParser.parse_with_model(
            file_data.extracted_text,
            request.model_id.value
        )
        
        # Log the result structure for debugging
        logger.info(f"Result from TextParser: {result}")
        
        # Ensure result has the expected structure
        if not isinstance(result, dict):
            raise ValueError(f"Expected dict result, got {type(result)}")
            
        # Get parsed_content with fallback
        parsed_content = result.get('parsed_content', result)
        model_info = result.get('model_info', {'provider': 'unknown', 'model': request.model_id.value})

        # Remove original_text if it exists in parsed_content
        if isinstance(parsed_content, dict):
            parsed_content.pop('original_text', None)

        # Create database-ready parsed result
        db_parsed_result = {
            "content": parsed_content,
            "model": {
                "id": request.model_id.value,
                "info": model_info
            },
            "metadata": {
                "processing_timestamp": datetime.utcnow().isoformat()
            }
        }

        # Update database with parsed result
        await FileService.update_parsed_file(
            request.file_id,
            db_parsed_result,
            request.model_id.value
        )

        # Return response following Refine patterns
        return {
            "data": {
                "id": str(request.file_id),
                "status": "completed",
                "success": True,
                "model": {
                    "id": request.model_id.value,
                    "info": model_info
                },
                "result": parsed_content,
                "metadata": {
                    "original_text_length": len(file_data.extracted_text),
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
            },
            "error": None
        }

    except Exception as e:
        logger.error(f"Error in parse_text: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error("Error traceback: ", exc_info=True)
        return {
            "data": {
                "id": str(request.file_id),
                "status": "failed",
                "success": False
            },
            "error": {
                "code": 500,
                "message": str(e)
            }
        }

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