from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from utils.pdf_processor import PDFProcessor

router = APIRouter(
    prefix="/pdf",
    tags=["pdf"],
    responses={404: {"description": "Not found"}},
)

class PDFReadRequest(BaseModel):
    """Request model for PDF reading endpoints"""
    file_path: Optional[str] = None  # For testing phase
    storage_id: Optional[str] = None  # For production phase

@router.post("/extract-text")
async def extract_text(request: PDFReadRequest):
    """
    Extract text content from a PDF file.
    
    Args:
        request (PDFReadRequest): Request containing either file_path or storage_id
        
    Returns:
        dict: Contains extracted text and metadata
    """
    if not request.file_path and not request.storage_id:
        raise HTTPException(
            status_code=400,
            detail="Either file_path or storage_id must be provided"
        )
    
    # For testing phase
    if request.file_path:
        return await PDFProcessor.extract_text_from_pdf(request.file_path)
    
    # For production phase (implement Firebase storage integration)
    # TODO: Implement Firebase storage retrieval
    raise HTTPException(
        status_code=501,
        detail="Firebase storage integration not implemented yet"
    ) 