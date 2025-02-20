import logging
from typing import List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database.models import ParsingResult, MatchingUnit, ConfirmationFile, FileStatusHistory, ProcessingStatus
from database.database import get_db

logger = logging.getLogger(__name__)

class ExtractMatchingUnitService:
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

                # Extract transactions from parsed data - handle different possible structures
                parsed_content = file.parsed_data
                if isinstance(parsed_content, dict):
                    # Navigate through possible nested structures
                    for key in ['parsed_result', 'content', 'parsed_content']:
                        if key in parsed_content:
                            parsed_content = parsed_content[key]
                
                transactions = parsed_content.get('transactions', [])
                if not transactions:
                    logger.error(f"No transactions found in parsed content structure: {parsed_content}")
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
                        matching_unit = MatchingUnit(
                            file_id=file_id,
                            extracted_transactions={
                                'pay_leg': pay_leg,
                                'receive_leg': receive_leg,
                                'trade_type': parsed_content.get('TradeType'),
                                'trade_date': parsed_content.get('TradeDate'),
                                'settlement_date': settle_date,
                                'trading_party_code': parsed_content.get('TradingParty'),
                                'counterparty_code': parsed_content.get('CounterParty'),
                                'trade_ref': parsed_content.get('TradeRef'),
                                'trade_uti': parsed_content.get('TradeUTI')
                            }
                        )
                        db.add(matching_unit)
                        await db.flush()  # Flush to get the generated ID
                        matching_unit_ids.append(matching_unit.matching_unit_id)

                # Create status history record
                status_history = FileStatusHistory(
                    file_id=file_id,
                    previous_status=ProcessingStatus.TEXT_PARSED,
                    new_status=ProcessingStatus.UNITS_CREATED,
                    trigger_source="api/extract-matching-units",
                    additional_data={
                        "matching_unit_ids": [str(id) for id in matching_unit_ids],
                        "total_units_created": len(matching_unit_ids)
                    }
                )
                db.add(status_history)

                # Update file status and counts
                file.processing_status = ProcessingStatus.UNITS_CREATED
                file.total_matching_units = len(matching_unit_ids)
                file.matched_units_count = 0  # Reset matched count

                await db.commit()
                logger.info(f"Successfully created {len(matching_unit_ids)} matching units")
                return matching_unit_ids

            except Exception as e:
                await db.rollback()
                logger.error(f"Error during matching unit extraction: {str(e)}")
                raise 