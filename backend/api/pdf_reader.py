from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any
from pydantic import BaseModel, UUID4, Field
from utils.pdf_processor import PDFProcessor
from database.database import get_db
from database.models import ConfirmationFile, FileStatusHistory, ProcessingStatus
from enum import Enum
from sqlalchemy import select, update, and_
from datetime import datetime
from services.file_service import FileService
from utils.text_parser import TextParser
from services.model_service import ModelFactory
import logging
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pdf"],
    responses={404: {"description": "Not found"}}
)

@router.get("/test-model-connection")
async def test_model_connection():
    """Test the model API connection"""
    try:
        service = ModelFactory.get_model_service("nvidia_deepseek_r1")
        result = await service.parse_text("Test connection")
        return {"status": "success", "message": "Model connection successful"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model connection test failed: {str(e)}"
        )

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify router configuration"""
    logger.debug("Test endpoint called")
    return {"message": "PDF reader router is working"}

@router.get("/")
async def root():
    """Root endpoint to verify router is mounted"""
    logger.debug("Root endpoint called")
    return {"message": "PDF reader router root endpoint"} 