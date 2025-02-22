from typing import Dict, Any
import logging
from fastapi import HTTPException, status
from sqlalchemy import select, and_
from database.models import ConfirmationFile, FileStatusHistory, ProcessingStatus
from database.database import get_db
from utils.text_parser import TextParser
from datetime import datetime

logger = logging.getLogger(__name__)

class ParseTextService:
    """Service for handling text parsing operations"""

    async def parse_text(
        self,
        file_id: str,
        model_id: str
    ) -> Dict[str, Any]:
        """
        Parse text from a confirmation file using specified AI model.
        
        Args:
            file_id (str): UUID of the file to process
            model_id (str): ID of the AI model to use
            
        Returns:
            Dict[str, Any]: Parsing results and metadata
            
        Raises:
            HTTPException: If file not found, invalid status, or parsing fails
        """
        logger.info(f"ParseTextService processing file_id: {file_id}")
        
        async with get_db() as db:
            try:
                # Lock the file row and verify status
                query = select(ConfirmationFile).where(
                    and_(
                        ConfirmationFile.file_id == file_id,
                        ConfirmationFile.processing_status == ProcessingStatus.TEXT_EXTRACTED
                    )
                ).with_for_update()
                
                result = await db.execute(query)
                file = result.scalar_one_or_none()
                
                if not file:
                    logger.warning(f"File not found or invalid status: {file_id}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File not found or not in TEXT_EXTRACTED status"
                    )

                logger.debug(f"Found file: {file.file_id}, status: {file.processing_status}")
                
                # Parse text with model
                parsed_data = await TextParser.parse_with_model(
                    text=file.extracted_text,
                    model_id=model_id
                )
                logger.debug("Text parsing successful")

                # Prepare response data
                response_data = {
                    "message": "Text parsing completed successfully",
                    "file_id": str(file.file_id),
                    "status": ProcessingStatus.TEXT_PARSED.value,
                    "parsed_data": parsed_data
                }

                # Create status history record
                status_history = FileStatusHistory(
                    file_id=file.file_id,
                    previous_status=ProcessingStatus.TEXT_EXTRACTED,
                    new_status=ProcessingStatus.TEXT_PARSED,
                    trigger_source="parse_text_service",
                    additional_data={
                        "request": {
                            "file_id": str(file_id),
                            "model_id": model_id
                        },
                        "response": response_data,
                        "model_info": parsed_data.get("model_info", {}),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                db.add(status_history)

                # Update file record
                file.parsed_data = parsed_data
                file.processing_status = ProcessingStatus.TEXT_PARSED

                await db.commit()
                return response_data

            except HTTPException:
                await db.rollback()
                raise
            except Exception as e:
                await db.rollback()
                logger.error(f"Error in parse_text: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error parsing text: {str(e)}"
                )
