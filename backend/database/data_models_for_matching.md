# Data Models for Matching Process

This project uses a PostgreSQL schema that supports the matching process via four main tables:

All API calls have to provide the allowed transitions in processing_status in confirmation_files table and the new status.
All API calls have to check the processing_status before performing the database update action.

1. **Confirmation Files**  
   - Stores each file upload with metadata and parsed content
   - **Key Fields:**  
     - `file_id`: Primary key  
     - `file_name`: Name of the file  
     - `file_path`: Local storage path (optional)  
     - `gcs_file_id`: Google Cloud Storage identifier
     - `extracted_text`: Raw text content from PDF
     - `parsed_data`: JSONB field with structured data from parsing
     - `processing_status`: Current processing state:
       - `Not_Processed`: Initial state
       - `TEXT_EXTRACTED`: Text extraction completed
       - `TEXT_PARSED`: Parsing completed
       - `UNITS_CREATED`: Matching units generated
       - `PARTIALLY_MATCHED`: Some units matched
       - `FULLY_MATCHED`: All units matched
       - `ERROR`: Processing error
     - `total_matching_units`: Count of matching units (updated when units are created)
     - `matched_units_count`: Count of matched units (updated when matches are made)
     - `created_at`: Record creation timestamp
     - `updated_at`: Last modification timestamp
   - **Constraints:**  
     - UniqueConstraint('file_name', 'file_path', 'gcs_file_id', name='unique_file_identifier')
   - **Status Management:**
     - Status transitions must follow the defined sequence
     - Each status change must be recorded in file_status_history
     - `UNITS_CREATED` status prevents duplicate unit creation
     - Unit counts must be updated atomically with related operations

2. **File Status History**
   - Tracks all state transitions and data changes
   - **Key Fields:**
     - `history_id`: Primary key
     - `file_id`: Foreign key to confirmation_files
     - `previous_status`: Previous workflow status
     - `new_status`: New workflow status
     - `transition_time`: When the change occurred
     - `trigger_source`: What caused the change (API endpoint, background job, etc)
     - `additional_data`: JSONB field storing:
       - Previous and new parsed_data when parsing changes
       - Matching unit counts
       - Error details
       - Other relevant metadata
   - **Constraints:**
     - Foreign key (file_id) REFERENCES confirmation_files ON DELETE CASCADE
   - **Usage:**
     - Every status change must create a history record
     - All significant data changes should be recorded
     - Provides audit trail for troubleshooting

3. **Matching Units**  
   - Individual units for matching
   - **Key Fields:**
     - `matching_unit_id`: Primary key
     - `file_id`: Foreign key to confirmation_files
     - `is_matched`: Boolean indicating if unit is matched
     - `created_at`: Record creation timestamp
     - `updated_at`: Last modification timestamp
     - `trade_type`: Type of trade, from parsed_data
     - `trade_date`: Date of trade, from parsed_data
     - `settlement_date`: Settlement date, from parsed_data
     - `trading_party_code`: Code for trading party, from party_codes
     - `counterparty_code`: Code for counter party, from party_codes
     - `trade_ref`: Trade reference number, from parsed_data
     - `settlement_rate`: Settlement rate if applicable, from parsed_data
     - `transaction_details`: JSONB field storing Pay/receive leg details, from parsed_data
        - `pay-leg`: pay leg details
          - `amount`: amount
          - `currency`: currency
        - `receive-leg`: receive leg details
          - `amount`: amount
          - `currency`: currency
   - **Constraints:**
     - Foreign key (file_id) REFERENCES confirmation_files ON DELETE CASCADE
   - **Usage:**
     - Can only be created when file status is 'TEXT_PARSED'
     - Creation must update file's total_matching_units
     - Matching must update file's matched_units_count

4. **Matching Relationships**  
   - Links between matched units
   - **Key Fields:**
     - `relationship_id`: Primary key
     - `matching_unit_1`: Foreign key to first matching unit
     - `matching_unit_2`: Foreign key to second matching unit
     - `created_at`: Record creation timestamp
   - **Constraints:**
     - UniqueConstraint('matching_unit_1', 'matching_unit_2', name='unique_matching_relationship')
   - **Usage:**
     - Creating/deleting relationships must update unit is_matched status
     - Must update file's matched_units_count
     - Should trigger file status update if all units matched

5. **Party Codes**  
    - Unique code for trading and counterpart parties   
    **Key Fields:**:
        party_code_id (UUID): Primary key
        party_code (str): code for the party, cannot be null
        msger_name (str): Name from MsgSender/MsgReceiver, from parsed_data
        msger_address (str): Address from MsgSender/MsgReceiver, from parsed_data
        party_name (str): Name from TradingParty/CounterParty, from parsed_data
        party_role (str): Role of the party (bank/corporate), can be null
        is_active (bool): Status flag, default is True
   - **Constraints:**
       - UniqueConstraint('msger_name', 'msger_address','party_name', 'party_role', name='unique_party_combination')

## Workflow Enforcement

1. **Status Transitions:**
   ```sql
   -- Example of safe status update with history
   BEGIN;
     -- Lock the file row
     SELECT * FROM confirmation_files 
     WHERE file_id = ? FOR UPDATE;
     
     -- Insert history record
     INSERT INTO file_status_history (...) VALUES (...);
     
     -- Update status and counts
     UPDATE confirmation_files 
     SET processing_status = ?, 
         total_matching_units = ?,
         matched_units_count = ?,
         updated_at = CURRENT_TIMESTAMP
     WHERE file_id = ?;
   COMMIT;
   ```

2. **One-to-Many Relationships:**
   - One confirmation file to many matching units
   - One matching unit to many relationships
   - One relationship to two matching units

3. **Cascading Updates - normal:**
   - CANNOT delete a file if it has matching units
   - CANNOT delete a matching unit if it has relationships

4. **Safe delete:**
   - Deleting is not allowed if there are related records in other tables.

 
