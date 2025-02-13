from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel, UUID4
from utils.pdf_processor import PDFProcessor
from database.database import get_db
from database.models import ConfirmationFile
from enum import Enum
from sqlalchemy import select

router = APIRouter(
    prefix="/pdf",
    tags=["pdf"],
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