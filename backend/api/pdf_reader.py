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

router = APIRouter(
    prefix="/api",
    tags=["api"],
    responses={404: {"description": "Not found"}},
)

class LocationType(str, Enum):
    """Enum for file location types"""
    LOCAL = "local"
    CLOUD = "cloud"

class PDFReadRequest(BaseModel):
    """Request model for PDF reading endpoints"""
    file_id: UUID4
    location: LocationType

class ParseTextRequest(BaseModel):
    """Request model for text parsing endpoint"""
    file_id: UUID4
    model_id: str = 'deepseek_r1'

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
    """Parse extracted text using specified model"""
    try:
        file_data = await FileService.get_extracted_file(request.file_id)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        if file_data.processing_status != 'extracted':
            raise HTTPException(status_code=400, detail="File text not yet extracted")
        if not file_data.extracted_text:
            raise HTTPException(status_code=404, detail="No extracted text found")

        # Get both parsed result and original text
        result = await TextParser.parse_with_model(
            file_data.extracted_text,
            request.model_id
        )

        # Update database with parsed result only
        await FileService.update_parsed_file(
            request.file_id,
            result['parsed_result'],  # Store only the parsed portion
            request.model_id
        )

        return {
            'success': True,
            'data': result  # Return both original text and parsed result
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 