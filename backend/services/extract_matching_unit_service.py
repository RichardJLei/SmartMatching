import logging
from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database.models import ParsingResult, MatchingUnit
from database.database import get_db

logger = logging.getLogger(__name__)

class ExtractMatchingUnitService:
    async def extract_matching_units(self, parsing_result_id: UUID) -> List[UUID]:
        """
        Extract matching units from parsed content and save to matching_units table.
        Only processes the latest parsing result.
        Returns list of created matching unit IDs.
        """
        logger.info(f"Starting extraction for parsing_result_id: {parsing_result_id}")
        
        async with get_db() as db:
            try:
                # Get parsing result using async query
                query = select(ParsingResult).where(
                    ParsingResult.parsing_result_id == parsing_result_id,
                    ParsingResult.latest == True  # Only process latest version
                )
                result = await db.execute(query)
                parsing_result = result.scalar_one_or_none()
                
                if not parsing_result:
                    logger.error(f"Latest parsing result not found for id: {parsing_result_id}")
                    raise ValueError("Latest parsing result not found")

                if not parsing_result.parsed_data:
                    logger.error(f"Parsed data is empty for parsing result: {parsing_result_id}")
                    raise ValueError("Parsed data is empty")

                # Navigate through the nested structure to get parsed content
                parsed_content = parsing_result.parsed_data
                if 'content' in parsed_content:
                    parsed_content = parsed_content['content']
                if 'parsed_result' in parsed_content:
                    parsed_content = parsed_content['parsed_result']
                if 'parsed_content' in parsed_content:
                    parsed_content = parsed_content['parsed_content']

                logger.debug(f"Extracted content structure: {parsed_content}")
                
                if 'transactions' not in parsed_content:
                    logger.error(f"No transactions found in content: {parsed_content}")
                    raise ValueError("No transactions found in parsed content")

                # Group transactions by settlement date
                settlement_groups = {}
                for trans in parsed_content['transactions']:
                    settle_date = trans['SettlementDate']
                    if settle_date not in settlement_groups:
                        settlement_groups[settle_date] = []
                    settlement_groups[settle_date].append(trans)
                
                logger.info(f"Found {len(settlement_groups)} settlement date groups")

                # Create matching units for each settlement date
                matching_unit_ids = []
                for settle_date, transactions in settlement_groups.items():
                    logger.debug(f"Processing settlement date: {settle_date}")
                    
                    # Find pay and receive legs
                    pay_leg = next((t for t in transactions if t['BuyrOrSell'] == 'Sell'), None)
                    receive_leg = next((t for t in transactions if t['BuyrOrSell'] == 'Buy'), None)
                    
                    if pay_leg and receive_leg:
                        logger.debug(f"Creating matching unit for date: {settle_date}")
                        # Create matching unit record
                        matching_unit = MatchingUnit(
                            parsing_result_id=parsing_result_id,
                            extracted_transactions={
                                'pay_leg': pay_leg,
                                'receive_leg': receive_leg,
                                'trade_type': parsed_content.get('TradeType'),
                                'trade_date': pay_leg['TradeDate'],
                                'settlement_date': settle_date,
                                'trading_party_code': parsed_content.get('TradingParty'),
                                'counterparty_code': parsed_content.get('CounterParty'),
                                'trade_ref': parsed_content.get('TradeRef'),
                                'trade_uti': parsed_content.get('TradeUTI'),
                                'settlement_rate': parsed_content.get('SettlementRate')
                            }
                        )
                        
                        db.add(matching_unit)
                        await db.flush()
                        matching_unit_ids.append(matching_unit.matching_unit_id)

                await db.commit()
                logger.info(f"Successfully created {len(matching_unit_ids)} matching units")
                return matching_unit_ids
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error during matching unit extraction: {str(e)}")
                raise 