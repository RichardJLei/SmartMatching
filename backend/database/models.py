from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import DefaultClause
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ConfirmationFile(Base):
    """
    Model for storing confirmation file data and processing status.
    
    Attributes:
        file_id (UUID): Primary key, unique identifier
        file_name (str): Original file name
        file_path (str): Local storage path (optional)
        gcs_file_id (str): Google Cloud Storage identifier
        extracted_text (str): Raw text content from PDF
        processing_status (str): Current processing state
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
        parsing_results (relationship): Related parsing results
    """
    __tablename__ = "confirmation_files"
    
    file_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    file_name = Column(String(255))
    file_path = Column(Text, nullable=True)
    gcs_file_id = Column(String(255))
    extracted_text = Column(Text)
    processing_status = Column(String(50), default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to parsing results
    parsing_results = relationship("ParsingResult", back_populates="file", cascade="all, delete")

class ParsingResult(Base):
    """
    Model for storing parsed results from confirmation files.
    
    Attributes:
        parsing_result_id (UUID): Primary key, unique identifier
        file_id (UUID): Foreign key to confirmation_files
        parsed_json (dict): Structured data from parsing
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
        file (relationship): Related confirmation file
    """
    __tablename__ = "parsing_results"
    
    parsing_result_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    file_id = Column(UUID(as_uuid=True), ForeignKey('confirmation_files.file_id', ondelete='CASCADE'), nullable=False)
    parsed_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to confirmation file
    file = relationship("ConfirmationFile", back_populates="parsing_results")

class EntityNames(Base):
    __tablename__ = 'entity_names'

    long_name_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    short_name = Column(String)
    long_name = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 