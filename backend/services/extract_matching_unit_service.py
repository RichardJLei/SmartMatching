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
        Returns list of created matching unit IDs.
        """
        logger.info(f"Starting extraction for parsing_result_id: {parsing_result_id}")
        
        async with get_db() as db:
            try:
                # Get parsing result using async query
                query = select(ParsingResult).where(
                    ParsingResult.parsing_result_id == parsing_result_id
                )
                result = await db.execute(query)
                parsing_result = result.scalar_one_or_none()
                
                if not parsing_result or not parsing_result.parsed_json:
                    logger.error(f"Parsing result not found or empty for id: {parsing_result_id}")
                    raise ValueError("Parsing result not found or empty")

                # Log the full parsed_json structure for debugging
                logger.debug(f"Full parsed_json structure: {parsing_result.parsed_json}")

                # Navigate through the nested structure
                parsed_content = parsing_result.parsed_json
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
                            matching_status='unmatched',
                            trade_type=parsed_content.get('TradeType'),
                            trade_date=datetime.strptime(pay_leg['TradeDate'], '%Y-%m-%d'),
                            settlement_date=datetime.strptime(settle_date, '%Y-%m-%d'),
                            trading_party_code=parsed_content.get('TradingParty'),
                            counterparty_code=parsed_content.get('CounterParty'),
                            trade_ref=parsed_content.get('TradeRef'),
                            trade_uti=parsed_content.get('TradeUTI'),
                            settlement_rate=parsed_content.get('SettlementRate'),
                            transaction_details={
                                'pay_leg': pay_leg,
                                'receive_leg': receive_leg
                            }
                        )
                        
                        db.add(matching_unit)
                        await db.flush()
                        matching_unit_ids.append(matching_unit.matching_unit_id)

                # Convert UUIDs to strings for JSON storage
                matching_unit_ids_str = [str(uid) for uid in matching_unit_ids]
                
                # Update parsing result with matching unit IDs
                parsing_result.matching_unit_ids = matching_unit_ids_str
                
                await db.commit()
                logger.info(f"Successfully created {len(matching_unit_ids)} matching units")
                return matching_unit_ids
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error during matching unit extraction: {str(e)}")
                raise 