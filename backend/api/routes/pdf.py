import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from pydantic import BaseModel

from services.extract_matching_unit_service import ExtractMatchingUnitService

logger = logging.getLogger(__name__)
router = APIRouter()

class ExtractMatchingUnitsRequest(BaseModel):
    parsing_result_id: UUID

class ExtractMatchingUnitsResponse(BaseModel):
    matching_unit_ids: List[UUID]

@router.post("/extract-matching-units-from-parsed-content", 
            response_model=ExtractMatchingUnitsResponse)
async def extract_matching_units(
    request: ExtractMatchingUnitsRequest
):
    """
    Extract matching units from parsed content and save to matching_units table.
    """
    logger.info(f"Received request for parsing_result_id: {request.parsing_result_id}")
    try:
        service = ExtractMatchingUnitService()
        matching_unit_ids = await service.extract_matching_units(
            request.parsing_result_id
        )
        logger.info(f"Successfully processed request. Created {len(matching_unit_ids)} matching units")
        return ExtractMatchingUnitsResponse(matching_unit_ids=matching_unit_ids)
    except ValueError as e:
        logger.error(f"ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 