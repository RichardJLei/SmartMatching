from typing import Dict, Union
import os
from PyPDF2 import PdfReader
from fastapi import HTTPException
from database.models import ConfirmationFile
from database.database import get_db
from uuid import UUID
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Utility class for processing PDF files and extracting text content."""
    
    @staticmethod
    async def extract_text_from_pdf(file_id: UUID, file_path: str, file_name: str) -> Dict[str, Union[str, int, bool]]:
        """Extract text content from a PDF file and update database."""
        logger.info(f"Starting PDF text extraction for file: {file_name}")
        try:
            # Construct full file path
            full_file_path = os.path.join(file_path, file_name)
            logger.debug(f"Full file path: {full_file_path}")
            
            if not os.path.exists(full_file_path):
                logger.error(f"File not found at path: {full_file_path}")
                raise HTTPException(status_code=404, detail="File not found")
            
            if not full_file_path.lower().endswith('.pdf'):
                logger.error(f"Invalid file type for: {full_file_path}")
                raise HTTPException(status_code=400, detail="File must be a PDF")
            
            # Extract text from PDF
            logger.debug("Starting PDF text extraction...")
            reader = PdfReader(full_file_path)
            text_content = ""
            for page_num, page in enumerate(reader.pages, 1):
                logger.debug(f"Processing page {page_num}/{len(reader.pages)}")
                text_content += page.extract_text()
            
            logger.info(f"Successfully extracted text from {file_name}")
            return {
                "data": {
                    "id": str(file_id),
                    "status": "completed",
                    "success": True,
                    "message": f"Successfully extracted text from {file_name}",
                    "text_content": text_content,
                    "metadata": {
                        "page_count": len(reader.pages),
                        "file_size": os.path.getsize(full_file_path),
                        "text_length": len(text_content)
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
            return {
                "data": {
                    "id": str(file_id),
                    "status": "failed",
                    "success": False,
                    "message": f"Error processing PDF: {str(e)}",
                    "error": str(e)
                }
            } 