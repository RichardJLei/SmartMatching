from typing import Dict, Union
import os
from PyPDF2 import PdfReader
from fastapi import HTTPException
from database.models import ConfirmationFile
from database.database import async_session
import uuid

class PDFProcessor:
    """Utility class for processing PDF files and extracting text content."""
    
    @staticmethod
    async def extract_text_from_pdf(file_path: str) -> Dict[str, Union[str, int]]:
        """Extract text content from a PDF file and store in database."""
        print(f"Attempting to read file: {file_path}")
        print(f"Full path: {os.path.abspath(file_path)}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        if not file_path.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Invalid file format. Only PDF files are supported")
            
        try:
            reader = PdfReader(file_path)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text()
            
            # Store in database
            async with async_session() as session:
                file_record = ConfirmationFile(
                    file_name=os.path.basename(file_path),
                    file_path=file_path,
                    extracted_text=text_content,
                    processing_status='processed'
                )
                session.add(file_record)
                await session.commit()
                
            return {
                "file_id": str(file_record.file_id),
                "text_content": text_content,
                "page_count": len(reader.pages),
                "file_size": os.path.getsize(file_path)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}") 