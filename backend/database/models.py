from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, func, Integer, UniqueConstraint,
    Boolean, CheckConstraint, Index, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class ProcessingStatus(enum.Enum):
    """Enum for confirmation file processing status"""
    Not_Processed = "Not_Processed"
    TEXT_EXTRACTED = "TEXT_EXTRACTED"
    TEXT_PARSED = "TEXT_PARSED"
    UNITS_CREATED = "UNITS_CREATED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    FULLY_MATCHED = "FULLY_MATCHED"
    ERROR = "ERROR"

class ConfirmationFile(Base):
    """
    Model for storing confirmation file data and processing status.
    
    Attributes:
        file_id (UUID): Primary key, unique identifier
        file_name (str): Original file name
        file_path (str): Local storage path (optional)
        gcs_file_id (str): Google Cloud Storage identifier
        extracted_text (str): Raw text content from PDF
        parsed_data (JSONB): Structured data from parsing
        processing_status (str): Current processing state
        total_matching_units (int): Total number of matching units
        matched_units_count (int): Number of matched units
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
        matching_units (relationship): Related matching units
        status_history (relationship): Related status history
    """
    __tablename__ = "confirmation_files"
    
    file_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=True)
    gcs_file_id = Column(String(255))
    extracted_text = Column(Text)
    parsed_data = Column(JSONB)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.Not_Processed)
    total_matching_units = Column(Integer, default=0)
    matched_units_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    matching_units = relationship("MatchingUnit", back_populates="file", cascade="all, delete")
    status_history = relationship("FileStatusHistory", back_populates="file", cascade="all, delete")

    # Add unique constraint for file identifiers
    __table_args__ = (
        UniqueConstraint('file_name', 'file_path', 'gcs_file_id', name='unique_file_identifier'),
    )

class FileStatusHistory(Base):
    """Model for tracking file status changes and data updates."""
    __tablename__ = "file_status_history"
    
    history_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    file_id = Column(UUID(as_uuid=True), ForeignKey('confirmation_files.file_id', ondelete='CASCADE'), nullable=False)
    previous_status = Column(Enum(ProcessingStatus))
    new_status = Column(Enum(ProcessingStatus), nullable=False)
    transition_time = Column(DateTime(timezone=True), server_default=func.now())
    trigger_source = Column(String(255))  # API endpoint, background job, etc.
    additional_data = Column(JSONB)  # For storing metadata about the change
    
    # Relationship
    file = relationship("ConfirmationFile", back_populates="status_history")

class MatchingUnit(Base):
    """
    Model for storing extracted transactions from parsing results.
    
    Attributes:
        matching_unit_id (UUID): Primary key
        file_id (UUID): Foreign key to confirmation_files
        extracted_transactions (JSONB): Pay/receive leg details
        is_matched (bool): Marks if the unit is matched
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
    """
    __tablename__ = "matching_units"
    
    matching_unit_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    file_id = Column(UUID(as_uuid=True), ForeignKey('confirmation_files.file_id', ondelete='CASCADE'), nullable=False)
    extracted_transactions = Column(JSONB, nullable=False)
    is_matched = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    file = relationship("ConfirmationFile", back_populates="matching_units")
    relationships_as_unit_1 = relationship(
        "MatchingRelationship",
        foreign_keys="[MatchingRelationship.matching_unit_1]",
        back_populates="unit_1_rel"
    )
    relationships_as_unit_2 = relationship(
        "MatchingRelationship",
        foreign_keys="[MatchingRelationship.matching_unit_2]",
        back_populates="unit_2_rel"
    )

class MatchingRelationship(Base):
    """
    Model for storing relationships between matching units.
    
    Attributes:
        relationship_id (UUID): Primary key
        matching_unit_1 (UUID): Foreign key to first matching unit
        matching_unit_2 (UUID): Foreign key to second matching unit
        created_at (datetime): Record creation timestamp
    """
    __tablename__ = "matching_relationships"
    
    relationship_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    matching_unit_1 = Column(UUID(as_uuid=True), ForeignKey('matching_units.matching_unit_id'), nullable=False)
    matching_unit_2 = Column(UUID(as_uuid=True), ForeignKey('matching_units.matching_unit_id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    unit_1_rel = relationship("MatchingUnit", foreign_keys=[matching_unit_1], back_populates="relationships_as_unit_1")
    unit_2_rel = relationship("MatchingUnit", foreign_keys=[matching_unit_2], back_populates="relationships_as_unit_2")

    __table_args__ = (
        UniqueConstraint('matching_unit_1', 'matching_unit_2', name='unique_matching_relationship'),
    )

class PartyCode(Base):
    """
    Model for storing party information and their codes.
    
    Attributes:
        party_code_id (UUID): Primary key
        party_code (str): Generated unique code for the party
        msger_name (str): Name from MsgSender/MsgReceiver
        msger_address (str): Address from MsgSender/MsgReceiver
        party_name (str): Name from TradingParty/CounterParty
        party_role (str): Role of the party (bank/corporate)
        is_active (bool): Status flag
    """
    __tablename__ = "party_codes"
    
    party_code_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    party_code = Column(String(100), nullable=False)
    msger_name = Column(String(255), nullable=True)
    msger_address = Column(Text)
    party_name = Column(String(255), nullable=False)
    party_role = Column(String(50), nullable=False)  # 'bank' or 'corporate'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraints
    __table_args__ = (
        UniqueConstraint('party_code', name='unique_party_code'),
        UniqueConstraint('msger_name', 'party_name', 'party_role', name='unique_party_combination'),
    ) 