import logging
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from database.models import (
    ConfirmationFile, 
    MatchingUnit, 
    FileStatusHistory, 
    ProcessingStatus, 
    PartyCode
)
from database.database import get_db

logger = logging.getLogger(__name__)

class ExtractMatchingUnitsService:
    """Service for extracting matching units from parsed confirmation files"""

    async def _find_party_code(
        self, 
        db: AsyncSession,
        msger_name: Optional[str],
        msger_address: Optional[str],
        party_name: Optional[str]
    ) -> Tuple[Optional[str], dict]:
        """
        Find party code from party_codes table using message and party details.

        Args:
            db (AsyncSession): Database session
            msger_name (Optional[str]): Message sender/receiver name
            msger_address (Optional[str]): Message sender/receiver address
            party_name (Optional[str]): Trading/counter party name

        Returns:
            Tuple[Optional[str], dict]: (party_code, search_criteria)
        """
        search_criteria = {
            'msger_name': msger_name,
            'msger_address': msger_address,
            'party_name': party_name
        }
        
        conditions = []
        if msger_name:
            conditions.append(PartyCode.msger_name == msger_name)
        if msger_address:
            conditions.append(PartyCode.msger_address == msger_address)
        if party_name:
            conditions.append(PartyCode.party_name == party_name)
            
        if not conditions:
            return None, search_criteria
            
        query = select(PartyCode).where(or_(*conditions))
        result = await db.execute(query)
        party = result.scalar_one_or_none()
        
        return party.party_code if party else None, search_criteria

    async def _get_and_validate_file(
        self, 
        db: AsyncSession, 
        file_id: UUID
    ) -> ConfirmationFile:
        """
        Get and validate file exists and is in correct status.
        
        Args:
            db: Database session
            file_id: ID of file to process
            
        Returns:
            ConfirmationFile: The validated file record
            
        Raises:
            ValueError: If file not found or in wrong status
        """
        query = select(ConfirmationFile).where(
            and_(
                ConfirmationFile.file_id == file_id,
                ConfirmationFile.processing_status == ProcessingStatus.TEXT_PARSED
            )
        ).with_for_update()
        
        result = await db.execute(query)
        file = result.scalar_one_or_none()
        
        if not file:
            raise ValueError("File not found or not in TEXT_PARSED status")
            
        return file

    async def _validate_parsed_content(self, file: ConfirmationFile) -> Dict[str, Any]:
        """
        Validate parsed content exists and has required structure.
        
        Args:
            file: Confirmation file record
            
        Returns:
            Dict: The validated parsed content
            
        Raises:
            ValueError: If parsed content invalid or missing
        """
        if not file.parsed_data:
            raise ValueError("No parsed data found")

        parsed_content = file.parsed_data.get('parsed_result', {}).get('parsed_content', {})
        if not parsed_content:
            raise ValueError("Invalid parsed data structure")
            
        return parsed_content

    async def _get_trading_party_code(
        self, 
        db: AsyncSession, 
        parsed_content: Dict[str, Any]
    ) -> str:
        """Get and validate trading party code."""
        msg_sender = parsed_content.get('MsgSender', {})
        trading_party_code, trading_search = await self._find_party_code(
            db,
            msg_sender.get('Name'),
            msg_sender.get('Address'),
            parsed_content.get('TradingParty')
        )
        
        if not trading_party_code:
            raise ValueError(f"Trading party not found in party_codes table. Search criteria: {trading_search}")
            
        return trading_party_code

    async def _get_counter_party_code(
        self, 
        db: AsyncSession, 
        parsed_content: Dict[str, Any]
    ) -> str:
        """Get and validate counter party code."""
        msg_receiver = parsed_content.get('MsgReceiver', {})
        counter_party_code, counter_search = await self._find_party_code(
            db,
            msg_receiver.get('Name'),
            msg_receiver.get('Address'),
            parsed_content.get('CounterParty')
        )
        
        if not counter_party_code:
            raise ValueError(f"Counter party not found in party_codes table. Search criteria: {counter_search}")
            
        return counter_party_code

    async def _create_matching_units(
        self,
        db: AsyncSession,
        file: ConfirmationFile,
        parsed_content: Dict[str, Any],
        trading_party_code: str,
        counter_party_code: str
    ) -> List[UUID]:
        """Create matching units from parsed content."""
        trade_type = parsed_content.get('TradeType')
        trade_ref = parsed_content.get('TradeRef')
        settlement_rate = float(parsed_content.get('SettlementRate')) if parsed_content.get('SettlementRate') else None
        
        transactions = parsed_content.get('transactions', [])
        if not transactions:
            raise ValueError("No transactions found in parsed content")

        # Group transactions by settlement date
        settlement_groups = {}
        for trans in transactions:
            settle_date = trans.get('SettlementDate')
            if settle_date:
                if settle_date not in settlement_groups:
                    settlement_groups[settle_date] = []
                settlement_groups[settle_date].append(trans)

        matching_unit_ids = []
        
        # Create matching units for each settlement date
        for settle_date, grouped_trans in settlement_groups.items():
            pay_leg = next((t for t in grouped_trans if t.get('BuyrOrSell') == 'Sell'), None)
            receive_leg = next((t for t in grouped_trans if t.get('BuyrOrSell') == 'Buy'), None)
            
            if pay_leg and receive_leg:
                # Convert date strings to date objects
                trade_date = datetime.strptime(pay_leg['TradeDate'], '%Y-%m-%d').date()
                settlement_date = datetime.strptime(settle_date, '%Y-%m-%d').date()
                
                # Create transaction details JSONB
                transaction_details = {
                    'pay_leg': {
                        'amount': pay_leg['Amount'],
                        'currency': pay_leg['Currency']
                    },
                    'receive_leg': {
                        'amount': receive_leg['Amount'],
                        'currency': receive_leg['Currency']
                    }
                }

                matching_unit = MatchingUnit(
                    file_id=file.file_id,
                    is_matched=False,
                    trade_type=trade_type,
                    trade_date=trade_date,
                    settlement_date=settlement_date,
                    trading_party_code=trading_party_code,
                    counterparty_code=counter_party_code,
                    trade_ref=trade_ref,
                    settlement_rate=settlement_rate,
                    transaction_details=transaction_details
                )
                
                db.add(matching_unit)
                await db.flush()  # Flush to get the generated ID
                matching_unit_ids.append(matching_unit.matching_unit_id)
                
        return matching_unit_ids

    async def _update_file_status(
        self,
        db: AsyncSession,
        file: ConfirmationFile,
        matching_unit_ids: List[UUID]
    ) -> None:
        """Update file status and create history record."""
        file.total_matching_units = len(matching_unit_ids)
        file.processing_status = ProcessingStatus.UNITS_CREATED
        
        history = FileStatusHistory(
            file_id=file.file_id,
            previous_status=ProcessingStatus.TEXT_PARSED,
            new_status=ProcessingStatus.UNITS_CREATED,
            trigger_source='extract_matching_units_api',
            additional_data={
                'matching_unit_count': len(matching_unit_ids),
                'matching_unit_ids': [str(id) for id in matching_unit_ids]
            }
        )
        db.add(history)

    async def extract_matching_units(self, file_id: UUID) -> List[UUID]:
        """
        Extract matching units from parsed content and save to matching_units table.

        Args:
            file_id (UUID): ID of the confirmation file to process

        Returns:
            List[UUID]: List of created matching unit IDs

        Raises:
            ValueError: For validation errors or invalid file status
            Exception: For unexpected processing errors
        """
        logger.info(f"Starting matching unit extraction for file_id: {file_id}")
        
        async with get_db() as db:
            try:
                file = await self._get_and_validate_file(db, file_id)
                parsed_content = await self._validate_parsed_content(file)
                
                # Get party codes
                trading_party_code = await self._get_trading_party_code(db, parsed_content)
                counter_party_code = await self._get_counter_party_code(db, parsed_content)
                
                # Create matching units
                matching_unit_ids = await self._create_matching_units(
                    db, file, parsed_content, 
                    trading_party_code, counter_party_code
                )
                
                # Update file status
                await self._update_file_status(db, file, matching_unit_ids)
                
                await db.commit()
                logger.info(f"Created {len(matching_unit_ids)} matching units for file {file_id}")
                
                return matching_unit_ids

            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating matching units: {str(e)}")
                raise

    # Additional helper methods would go here...
    # (The rest of the implementation would be split into smaller, focused methods)
