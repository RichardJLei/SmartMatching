from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update
from database.models import ConfirmationFile, ParsingResult
from database.database import get_db
from fastapi import HTTPException

class FileService:
    """
    Service for file-related database operations.
    Handles file status tracking and content management.
    """
    
    @staticmethod
    async def get_extracted_file(file_id: str) -> Optional[ConfirmationFile]:
        """
        Retrieve a file that has completed text extraction.
        
        Args:
            file_id (str): UUID of the file to retrieve
            
        Returns:
            Optional[ConfirmationFile]: File record if found and extracted, None otherwise
            
        Raises:
            HTTPException: If database operation fails
        """
        async with get_db() as db:
            try:
                query = select(ConfirmationFile).where(
                    ConfirmationFile.file_id == file_id
                )
                result = await db.execute(query)
                file_data = result.scalar_one_or_none()
                
                if not file_data:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No file found with ID: {file_id}"
                    )
                
                if file_data.processing_status != 'extracted':
                    raise HTTPException(
                        status_code=400,
                        detail=f"File status is '{file_data.processing_status}', expected 'extracted'"
                    )
                
                return file_data
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error while retrieving file: {str(e)}"
                )
    
    @staticmethod
    async def update_parsed_file(
        file_id: str,
        parsed_result: Dict[str, Any],
        model_id: str
    ) -> None:
        """
        Update file record with parsed results.
        
        Args:
            file_id (str): UUID of the file to update
            parsed_result (Dict[str, Any]): Structured data extracted from the file
            model_id (str): Identifier of the model used for parsing
            
        Raises:
            HTTPException: If update operation fails
        """
        async with get_db() as db:
            try:
                
                # Create new parsing result
                new_parsing_result = ParsingResult(
                    file_id=file_id,
                    parsed_json=parsed_result
                )
                db.add(new_parsing_result)
                
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update file: {str(e)}"
                ) 