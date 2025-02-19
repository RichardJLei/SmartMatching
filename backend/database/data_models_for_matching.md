# Data Models for Matching Process

This project uses a PostgreSQL schema that supports the matching process via four main tables:

1. **Confirmation Files**  
   - Stores each file upload with basic metadata.
   - **Key Fields:**  
     - `id`: Primary key.  
     - `file_name`: Name of the file.  
     - `file_path`: Local storage path (optional)  
     - `gcs_file_id`: Google Cloud Storage identifier  
     - `processing_status`: Indicates if the file is pending, processed, or in error.  
     - `created_at`: Timestamp when the file was added.
   - **Constraints:**  
     - Unique combination of file_name, file_path, and gcs_file_id prevents duplicate file entries

2. **Parsing Results**  
   - Contains parsed data (JSONB) from a confirmation file.  
   - Supports versioning:  
     - `version`: Tracks the version of the parsing result (default is 1).  
     - `latest`: A boolean flag marking the most recent parsing result for a file.
   - A unique index ensures only one parsing result per confirmation file is marked as latest.
   - **Workflow:**  
     - When updating parsing for a file, mark the previous result as non-latest and insert a new record with an increased version.

3. **Matching Units**  
   - Stores the extracted transactions used for matching.
   - **Key Field:**  
     - `extracted_transactions`: A JSONB field storing transaction data.
   - Each matching unit is linked to a parsing result (typically the latest from a given file).

4. **Matching Relationships**  
   - Maintains the links (relationships) between extracted matching units.
   - **Key Fields:**  
     - `matching_unit_1` and `matching_unit_2`: Foreign keys to matching units.
   - A unique constraint prevents cyclic or duplicate relationships between the same pair of units.

## Common Operations

1. **Insert a New Confirmation File:**  
   - Use an INSERT statement to add a new record to the confirmation_files table, then use its `id` for subsequent operations.

2. **Insert a New Parsing Result:**  
   - Update any previous parsing result for the file (set `latest` to FALSE) and insert a new record with the current parsed data, incrementing the version and setting `latest` to TRUE.

3. **Insert a New Matching Unit:**  
   - With the latest parsing result ID, insert a matching unit containing the extracted transactions.
   - In our models, the foreign keys for MatchingRelationship are defined with ondelete='CASCADE'.
        - This means that if a matching unit is deleted, any relationship entries referring to it will be automatically removed from the database.
        - This approach ensures that orphaned references do not remain, but it does not stop the deletion of a matching unit that still has relationships.

4. **Create a Matching Relationship:**  
   - Insert a new record into matching_relationships linking two matching units.
   - The unique constraint ensures that duplicate relationships are not created.

5. **Safe Deletion:**  
   - Before a matching unit is deleted, ensure that its relationships are removed.
   - The business logic (or triggers in the database) prevents accidental deletion if references exist.

This structure maintains non-cyclic dependencies and efficient updates by marking the latest parsing results, while also ensuring safe deletions and clean matching relationships.