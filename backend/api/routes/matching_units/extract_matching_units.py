from fastapi import APIRouter, HTTPException, status
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
import logging
from services.matching_units.extract_matching_units_service import ExtractMatchingUnitsService
from database.models import ProcessingStatus

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["matching_units"],
    responses={404: {"description": "Not found"}},
    redirect_slashes=True
)

class ExtractMatchingUnitsRequest(BaseModel):
    """Request model for extracting matching units"""
    file_id: UUID = Field(
        ...,
        description="UUID of the confirmation file to process"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }

class ExtractMatchingUnitsResponse(BaseModel):
    """Response model for matching units extraction"""
    matching_unit_ids: List[UUID] = Field(
        ...,
        description="List of created matching unit UUIDs"
    )
    message: str = Field(
        ...,
        description="Success message with count of units created"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "matching_unit_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "message": "Successfully created 1 matching units"
            }
        }

@router.post(
    "/extract-matching-units-from-parsed-content",
    response_model=ExtractMatchingUnitsResponse,
    status_code=status.HTTP_200_OK,
    description="Extract matching units from a confirmation file's parsed content"
)
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
    
    Args:
        request (ExtractMatchingUnitsRequest): Request containing file_id
        
    Returns:
        ExtractMatchingUnitsResponse: Created matching unit IDs and success message
        
    Raises:
        HTTPException (400): For validation errors or invalid file status
        HTTPException (500): For unexpected processing errors
    """
    logger.info(f"Received request for file_id: {request.file_id}")
    
    try:
        service = ExtractMatchingUnitsService()
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
