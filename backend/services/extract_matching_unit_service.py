from typing import List
from uuid import UUID
import logging
from fastapi import HTTPException
from sqlalchemy import select, and_
from database.database import get_db
from database.models import MatchingUnit, ConfirmationFile, FileStatusHistory, ProcessingStatus

logger = logging.getLogger(__name__)

class ExtractMatchingUnitService:
    async def extract_matching_units(self, file_id: UUID) -> List[UUID]:
        """
        Extract matching units from a confirmation file's parsed content.
        
        Args:
            file_id (UUID): ID of the confirmation file to process
            
        Returns:
            List[UUID]: List of created matching unit IDs
            
        Raises:
            HTTPException: If file not found or processing fails
        """
        async with get_db() as db:
            try:
                # Get file with lock
                query = select(ConfirmationFile).where(
                    and_(
                        ConfirmationFile.file_id == file_id,
                        ConfirmationFile.processing_status == ProcessingStatus.TEXT_PARSED
                    )
                ).with_for_update()
                
                result = await db.execute(query)
                file = result.scalar_one_or_none()
                
                if not file:
                    raise ValueError(f"File {file_id} not found or not in TEXT_PARSED status")
                
                if not file.parsed_data:
                    raise ValueError(f"No parsed data found for file {file_id}")
                
                # Extract transactions from parsed data
                transactions = file.parsed_data.get("transactions", [])
                if not transactions:
                    raise ValueError("No transactions found in parsed content")
                
                # Create matching units
                matching_unit_ids = []
                for transaction in transactions:
                    matching_unit = MatchingUnit(
                        file_id=file_id,
                        extracted_transactions=transaction
                    )
                    db.add(matching_unit)
                    await db.flush()  # Get the ID
                    matching_unit_ids.append(matching_unit.matching_unit_id)
                
                # Create status history record
                status_history = FileStatusHistory(
                    file_id=file_id,
                    previous_status=ProcessingStatus.TEXT_PARSED,
                    new_status=ProcessingStatus.UNITS_CREATED,
                    trigger_source="api/extract-matching-units",
                    additional_data={
                        "matching_unit_ids": [str(id) for id in matching_unit_ids],
                        "total_units_created": len(matching_unit_ids)
                    }
                )
                db.add(status_history)

                # Update file status and counts
                file.processing_status = ProcessingStatus.UNITS_CREATED
                file.total_matching_units = len(matching_unit_ids)
                file.matched_units_count = 0  # Reset matched count

                await db.commit()
                logger.info(f"Successfully created {len(matching_unit_ids)} matching units")
                return matching_unit_ids

            except Exception as e:
                await db.rollback()
                logger.error(f"Error during matching unit extraction: {str(e)}")
                raise 