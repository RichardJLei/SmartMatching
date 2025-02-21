import logging
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from database.models import ConfirmationFile, MatchingUnit, FileStatusHistory, ProcessingStatus, PartyCode
from database.database import get_db

logger = logging.getLogger(__name__)

class ExtractMatchingUnitService:
    async def _find_party_code(
        self, 
        db: AsyncSession,
        msger_name: Optional[str],
        msger_address: Optional[str],
        party_name: Optional[str]
    ) -> Tuple[Optional[str], dict]:
        """
        Find party code from party_codes table using message and party details.
        Returns tuple of (party_code, search_criteria).
        """
        search_criteria = {
            'msger_name': msger_name,
            'msger_address': msger_address,
            'party_name': party_name
        }
        
        # Build query conditions
        conditions = []
        if msger_name:
            conditions.append(PartyCode.msger_name == msger_name)
        if msger_address:
            conditions.append(PartyCode.msger_address == msger_address)
        if party_name:
            conditions.append(PartyCode.party_name == party_name)
            
        if not conditions:
            return None, search_criteria
            
        # Search with any matching condition
        query = select(PartyCode).where(or_(*conditions))
        result = await db.execute(query)
        party = result.scalar_one_or_none()
        
        return party.party_code if party else None, search_criteria

    async def extract_matching_units(self, file_id: UUID) -> List[UUID]:
        """
        Extract matching units from parsed content and save to matching_units table.
        Only processes files in TEXT_PARSED status.
        Returns list of created matching unit IDs.
        """
        logger.info(f"Starting matching unit extraction for file_id: {file_id}")
        
        async with get_db() as db:
            try:
                # Lock the file row and verify status
                query = select(ConfirmationFile).where(
                    and_(
                        ConfirmationFile.file_id == file_id,
                        ConfirmationFile.processing_status == ProcessingStatus.TEXT_PARSED
                    )
                ).with_for_update()
                
                result = await db.execute(query)
                file = result.scalar_one_or_none()
                
                if not file:
                    logger.error(f"File not found or not in TEXT_PARSED status: {file_id}")
                    raise ValueError("File not found or not in correct status")

                if not file.parsed_data:
                    logger.error(f"No parsed data found for file: {file_id}")
                    raise ValueError("No parsed data found")

                parsed_content = file.parsed_data.get('parsed_result', {}).get('parsed_content', {})
                if not parsed_content:
                    logger.error(f"Invalid parsed data structure: {file.parsed_data}")
                    raise ValueError("Invalid parsed data structure")

                # Find trading party code
                msg_sender = parsed_content.get('MsgSender', {})
                trading_party_code, trading_search = await self._find_party_code(
                    db,
                    msg_sender.get('Name'),
                    msg_sender.get('Address'),
                    parsed_content.get('TradingParty')
                )
                
                if not trading_party_code:
                    error_msg = f"Trading party not found in party_codes table. Search criteria: {trading_search}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                # Find counter party code
                msg_receiver = parsed_content.get('MsgReceiver', {})
                counter_party_code, counter_search = await self._find_party_code(
                    db,
                    msg_receiver.get('Name'),
                    msg_receiver.get('Address'),
                    parsed_content.get('CounterParty')
                )
                
                if not counter_party_code:
                    error_msg = f"Counter party not found in party_codes table. Search criteria: {counter_search}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                # Extract other common data from parsed content
                trade_type = parsed_content.get('TradeType')
                trade_ref = parsed_content.get('TradeRef')
                settlement_rate = float(parsed_content.get('SettlementRate')) if parsed_content.get('SettlementRate') else None
                
                transactions = parsed_content.get('transactions', [])
                if not transactions:
                    logger.error(f"No transactions found in parsed content")
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
                            file_id=file_id,
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

                # Update file status and counts
                file.total_matching_units = len(matching_unit_ids)
                file.processing_status = ProcessingStatus.UNITS_CREATED
                
                # Create status history record
                history = FileStatusHistory(
                    file_id=file_id,
                    previous_status=ProcessingStatus.TEXT_PARSED,
                    new_status=ProcessingStatus.UNITS_CREATED,
                    trigger_source='extract_matching_units_api',
                    additional_data={
                        'matching_unit_count': len(matching_unit_ids),
                        'matching_unit_ids': [str(id) for id in matching_unit_ids]
                    }
                )
                db.add(history)
                
                await db.commit()
                logger.info(f"Created {len(matching_unit_ids)} matching units for file {file_id}")
                
                return matching_unit_ids

            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating matching units: {str(e)}")
                raise 