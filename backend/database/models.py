from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .database import Base
from sqlalchemy.schema import DefaultClause
from sqlalchemy.sql.expression import text

class ConfirmationFile(Base):
    """
    Model for storing confirmation file data and processing status.
    
    Attributes:
        file_id (UUID): Primary key, unique identifier
        file_name (str): Original file name
        file_path (str): Local storage path (optional)
        gcs_file_id (str): Google Cloud Storage identifier
        extracted_text (str): Raw text content from PDF
        parsed_json (dict): Structured data following MT300 standard
        processing_status (str): Current processing state
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
    """
    __tablename__ = "confirmation_files"
    
    file_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    file_name = Column(String(255))
    file_path = Column(Text, nullable=True)
    gcs_file_id = Column(String(255))
    extracted_text = Column(Text)
    parsed_json = Column(JSONB)
    processing_status = Column(String(50), default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 