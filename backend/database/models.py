from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, func, Integer, UniqueConstraint,
    Boolean, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ConfirmationFile(Base):
    """
    Model for storing confirmation file data and processing status.
    
    Attributes:
        id (UUID): Primary key, unique identifier
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
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=True)
    gcs_file_id = Column(String(255))
    extracted_text = Column(Text)
    processing_status = Column(String(50), default='pending')  # pending, processed, error
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to parsing results
    parsing_results = relationship("ParsingResult", back_populates="file", cascade="all, delete")

    # Add unique constraint for file identifiers
    __table_args__ = (
        UniqueConstraint('file_name', 'file_path', 'gcs_file_id', name='unique_file_identifier'),
    )

class ParsingResult(Base):
    """
    Model for storing parsed results from confirmation files with versioning.
    
    Attributes:
        id (UUID): Primary key, unique identifier
        confirmation_file_id (UUID): Foreign key to confirmation_files
        parsed_data (dict): Structured data from parsing
        version (int): Tracks versions of parsing results
        latest (bool): Marks the latest parsing result
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
        file (relationship): Related confirmation file
        matching_units (relationship): Related matching units
    """
    __tablename__ = "parsing_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    confirmation_file_id = Column(UUID(as_uuid=True), ForeignKey('confirmation_files.id', ondelete='CASCADE'), nullable=False)
    parsed_data = Column(JSONB, nullable=False)
    version = Column(Integer, nullable=False, default=1)            # Tracks versions of parsing results
    latest = Column(Boolean, nullable=False, default=True)            # Marks the latest parsing result
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to confirmation file
    file = relationship("ConfirmationFile", back_populates="parsing_results")

    # Relationship to matching units
    matching_units = relationship("MatchingUnit", back_populates="parsing_result", cascade="all, delete")

    __table_args__ = (
        # Unique index to ensure only one latest parsing result per confirmation file
        Index('unique_latest_parsing_result', 'confirmation_file_id', unique=True, postgresql_where=text("latest")),
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

class MatchingUnit(Base):
    """
    Model for storing extracted transactions from parsing results.
    
    Attributes:
        matching_unit_id (UUID): Primary key
        parsing_result_id (UUID): Foreign key to parsing_results
        extracted_transactions (JSONB): Pay/receive leg details
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
    """
    __tablename__ = "matching_units"
    
    matching_unit_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    parsing_result_id = Column(UUID(as_uuid=True), ForeignKey('parsing_results.id', ondelete='CASCADE'), nullable=False)
    extracted_transactions = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to parsing result
    parsing_result = relationship("ParsingResult", back_populates="matching_units")

    # Relationships to matching relationships
    matching_relationships_from = relationship(
        "MatchingRelationship",
        foreign_keys="[MatchingRelationship.matching_unit_1]",
        cascade="all, delete",
        back_populates="matching_unit_1_rel"
    )
    matching_relationships_to = relationship(
        "MatchingRelationship",
        foreign_keys="[MatchingRelationship.matching_unit_2]",
        cascade="all, delete",
        back_populates="matching_unit_2_rel"
    )

class MatchingRelationship(Base):
    """
    Model for storing relationships between matching units.
    """
    __tablename__ = "matching_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    matching_unit_1 = Column(UUID(as_uuid=True), ForeignKey('matching_units.matching_unit_id', ondelete='CASCADE'), nullable=False)
    matching_unit_2 = Column(UUID(as_uuid=True), ForeignKey('matching_units.matching_unit_id', ondelete='CASCADE'), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('matching_unit_1', 'matching_unit_2', name='unique_matching_relationship'),
    )
    
    # Relationships back to MatchingUnit
    matching_unit_1_rel = relationship("MatchingUnit", foreign_keys=[matching_unit_1], back_populates="matching_relationships_from")
    matching_unit_2_rel = relationship("MatchingUnit", foreign_keys=[matching_unit_2], back_populates="matching_relationships_to") 