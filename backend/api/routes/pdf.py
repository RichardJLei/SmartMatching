import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from pydantic import BaseModel
from database.models import ProcessingStatus

from services.extract_matching_unit_service import ExtractMatchingUnitService

logger = logging.getLogger(__name__)
router = APIRouter()

class ExtractMatchingUnitsRequest(BaseModel):
    """Request model for extracting matching units"""
    file_id: UUID

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }

class ExtractMatchingUnitsResponse(BaseModel):
    """Response model for matching units extraction"""
    matching_unit_ids: List[UUID]
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "matching_unit_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "message": "Successfully created 1 matching units"
            }
        }

@router.post("/extract-matching-units-from-parsed-content", 
            response_model=ExtractMatchingUnitsResponse,
            status_code=status.HTTP_200_OK,
            tags=["PDF Processing"])
async def extract_matching_units(request: ExtractMatchingUnitsRequest):
    """
    Extract matching units from a confirmation file's parsed content.

    This endpoint processes a confirmation file and creates matching units from its transactions.
    Only processes files that are in TEXT_PARSED status.
    
    The process includes:
    1. Validating the file exists and is in TEXT_PARSED status
    2. Looking up party codes for both trading party and counter party
    3. Creating matching units for each settlement date's transactions
    4. Updating file status to UNITS_CREATED
    
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
        - When trading party code cannot be found in party_codes table
        - When counter party code cannot be found in party_codes table
    HTTPException (500)
        - When database operations fail
        - When unexpected errors occur

    State Changes:
    -------------
    - Creates new matching_units records
    - Updates confirmation_files status to UNITS_CREATED
    - Creates file_status_history record
    - Updates total_matching_units count in confirmation_files
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