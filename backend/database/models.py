from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Integer, UniqueConstraint, Boolean, CheckConstraint
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
        matching_units (relationship): Related matching units
    """
    __tablename__ = "parsing_results"
    
    parsing_result_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    file_id = Column(UUID(as_uuid=True), ForeignKey('confirmation_files.file_id', ondelete='CASCADE'), nullable=False)
    parsed_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to confirmation file
    file = relationship("ConfirmationFile", back_populates="parsing_results")

    # Add relationship to matching units
    matching_units = relationship("MatchingUnit", back_populates="parsing_result", cascade="all, delete")

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
    msger_name = Column(String(255), nullable=False)
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
    Model for storing matching units derived from parsing results.
    Each record represents one pair of pay & receive legs on the same settlement date.
    
    Attributes:
        matching_unit_id (UUID): Primary key
        parsing_result_id (UUID): Foreign key to parsing_results
        matching_status (str): Status of matching (unmatched/matched)
        trade_type (str): Type of trade
        trade_date (date): Date of trade
        settlement_date (date): Settlement date
        trading_party_code (str): Code for trading party
        counterparty_code (str): Code for counter party
        trade_ref (str): Trade reference number
        trade_uti (str): Unique trade identifier
        settlement_rate (str): Settlement rate if applicable
        transaction_details (JSONB): Pay/receive leg details
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
    """
    __tablename__ = "matching_units"
    
    matching_unit_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    parsing_result_id = Column(UUID(as_uuid=True), ForeignKey('parsing_results.parsing_result_id', ondelete='CASCADE'), nullable=False)
    matching_status = Column(String(50), nullable=False, default='unmatched')
    trade_type = Column(String(50))
    trade_date = Column(DateTime(timezone=True))
    settlement_date = Column(DateTime(timezone=True))
    trading_party_code = Column(String(100), nullable=False)
    counterparty_code = Column(String(100), nullable=False)
    trade_ref = Column(String(100))
    trade_uti = Column(String(255))
    settlement_rate = Column(String(50))
    transaction_details = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to parsing result
    parsing_result = relationship("ParsingResult", back_populates="matching_units")

    # Add constraints
    __table_args__ = (
        UniqueConstraint('trade_uti', name='unique_trade_uti'),
        CheckConstraint(
            "transaction_details ? 'pay_leg' AND transaction_details ? 'receive_leg'",
            name='check_transaction_details_structure'
        ),
        CheckConstraint(
            "matching_status IN ('unmatched', 'matched')",
            name='check_matching_status'
        )
    ) 