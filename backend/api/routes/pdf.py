import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from pydantic import BaseModel
from database.models import ProcessingStatus

from services.extract_matching_unit_service import ExtractMatchingUnitService

logger = logging.getLogger(__name__)
router = APIRouter()

class ExtractMatchingUnitsRequest(BaseModel):
    file_id: UUID

class ExtractMatchingUnitsResponse(BaseModel):
    matching_unit_ids: List[UUID]
    message: str

@router.post("/extract-matching-units-from-parsed-content", 
            response_model=ExtractMatchingUnitsResponse)
async def extract_matching_units(request: ExtractMatchingUnitsRequest):
    """
    Extract matching units from a confirmation file's parsed content.

    This endpoint processes a confirmation file and creates matching units from its transactions.
    Only processes files that are in TEXT_PARSED status.
    
    Parameters:
    -----------
    request : ExtractMatchingUnitsRequest
        Request body containing:
        - file_id: UUID of the confirmation file to process
    
    Returns:
    --------
    ExtractMatchingUnitsResponse
        Response containing:
        - matching_unit_ids: List of created matching unit UUIDs
        - message: Success message with count of units created

    Raises:
    -------
    HTTPException (400)
        - When file is not found
        - When file is not in TEXT_PARSED status
        - When no parsed data is found
        - When no transactions are found in parsed content
    HTTPException (500)
        - When database operations fail
        - When unexpected errors occur

    State Changes:
    -------------
    - Creates new matching_units records
    - Updates confirmation_files status to UNITS_CREATED
    - Creates file_status_history record
    """
    logger.info(f"Received request for file_id: {request.file_id}")
    try:
        service = ExtractMatchingUnitService()
        matching_unit_ids = await service.extract_matching_units(request.file_id)
        
        return ExtractMatchingUnitsResponse(
            matching_unit_ids=matching_unit_ids,
            message=f"Successfully created {len(matching_unit_ids)} matching units"
        )
    
    except ValueError as e:
        logger.error(f"ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 