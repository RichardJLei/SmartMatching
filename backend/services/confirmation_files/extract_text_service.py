from typing import Dict, Any
import logging
from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_
from database.models import ConfirmationFile, FileStatusHistory, ProcessingStatus
from database.database import get_db
from utils.pdf_processor import PDFProcessor
from api.routes.confirmation_files.types import LocationType

logger = logging.getLogger(__name__)

logger.debug(f"Available ProcessingStatus values: {[status.value for status in ProcessingStatus]}")

class ExtractTextService:
    """Service for handling text extraction from PDF files"""

    async def extract_text(
        self,
        file_id: str,
        location: LocationType
    ) -> Dict[str, Any]:
        """
        Extract text from a PDF file and update database.
        
        Args:
            file_id (str): UUID of the file to process
            location (LocationType): Storage location of the file
            
        Returns:
            Dict[str, Any]: Extraction results and metadata
            
        Raises:
            HTTPException: If file not found or processing fails
        """
        logger.info(f"ExtractTextService processing file_id: {file_id}")
        
        async with get_db() as db:
            try:
                # Modified query to handle NULL status correctly
                query = select(ConfirmationFile).where(
                    and_(
                        ConfirmationFile.file_id == file_id,
                        or_(
                            ConfirmationFile.processing_status.is_(None),
                            ConfirmationFile.processing_status == ProcessingStatus.Not_Processed
                        )
                    )
                ).with_for_update()
                
                # Log the query being executed
                logger.debug(f"Executing query: {query}")
                
                result = await db.execute(query)
                file_data = result.scalar_one_or_none()
                
                # Log the query result
                if file_data:
                    logger.debug(f"Found file data: ID={file_data.file_id}, "
                               f"Name={file_data.file_name}, "
                               f"Path={file_data.file_path}, "
                               f"Status={file_data.processing_status}")
                else:
                    # Check if file exists with different status
                    check_query = select(ConfirmationFile).where(
                        ConfirmationFile.file_id == file_id
                    )
                    check_result = await db.execute(check_query)
                    check_file = check_result.scalar_one_or_none()
                    
                    if check_file:
                        logger.error(f"File found but has invalid status: {check_file.processing_status}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File has invalid status: {check_file.processing_status}"
                        )
                    else:
                        logger.error("File not found in database")
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="File not found in database"
                        )

                if location == LocationType.LOCAL:
                    logger.debug(f"File path: {file_data.file_path}")
                    logger.debug(f"File name: {file_data.file_name}")
                    # Extract text using PDFProcessor utility
                    result = await PDFProcessor.extract_text_from_pdf(
                        file_id=file_id,
                        file_path=file_data.file_path,
                        file_name=file_data.file_name
                    )
                    
                    if result["data"]["success"]:
                        # Create status history record
                        status_history = FileStatusHistory(
                            file_id=file_data.file_id,
                            previous_status=file_data.processing_status,
                            new_status=ProcessingStatus.TEXT_EXTRACTED,
                            trigger_source="extract_text_service",
                            additional_data={
                                "request_params": {
                                    "file_id": str(file_id),
                                    "location": location.value
                                },
                                "extraction_metadata": result["data"].get("metadata", {})
                            }
                        )
                        db.add(status_history)
                        
                        # Update file record
                        file_data.extracted_text = result["data"]["text_content"]
                        file_data.processing_status = ProcessingStatus.TEXT_EXTRACTED
                        
                        await db.commit()
                        return result
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=result["data"].get("message", "Text extraction failed")
                        )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cloud storage not yet implemented"
                    )
                    
            except HTTPException:
                await db.rollback()
                raise
            except Exception as e:
                await db.rollback()
                logger.error(f"Error in extract_text service: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to extract text: {str(e)}"
                )
