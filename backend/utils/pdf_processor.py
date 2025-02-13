from typing import Dict, Union
import os
from PyPDF2 import PdfReader
from fastapi import HTTPException
from database.models import ConfirmationFile
from database.database import get_db
from uuid import UUID
from sqlalchemy import select

class PDFProcessor:
    """Utility class for processing PDF files and extracting text content."""
    
    @staticmethod
    async def extract_text_from_pdf(file_id: UUID, file_path: str, file_name: str) -> Dict[str, Union[str, int, bool]]:
        """Extract text content from a PDF file and update database."""
        # Construct full file path by joining path and filename
        full_file_path = os.path.join(file_path, file_name)
        
        print(f"Attempting to read file: {full_file_path}")
        print(f"Full path: {os.path.abspath(full_file_path)}")
        print(f"File exists: {os.path.exists(full_file_path)}")
        
        if not os.path.exists(full_file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        if not full_file_path.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Invalid file format. Only PDF files are supported")
            
        try:
            reader = PdfReader(full_file_path)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text()
            
            # Update using SQLAlchemy ORM
            async with get_db() as db:
                query = select(ConfirmationFile).where(ConfirmationFile.file_id == file_id)
                result = await db.execute(query)
                file_record = result.scalar_one_or_none()
                if file_record:
                    file_record.extracted_text = text_content
                    file_record.processing_status = 'extracted'
                    await db.commit()
            
            return {
                "data": {
                    "id": str(file_id),
                    "status": "completed",
                    "success": True,
                    "message": f"Successfully extracted text from {file_name}",
                    "metadata": {
                        "page_count": len(reader.pages),
                        "file_size": os.path.getsize(full_file_path)
                    }
                }
            }
        except Exception as e:
            return {
                "data": {
                    "id": str(file_id),
                    "status": "failed",
                    "success": False,
                    "message": f"Error processing PDF: {str(e)}",
                    "error": str(e)
                }
            } 