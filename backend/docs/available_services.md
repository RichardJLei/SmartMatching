# Available Services and Functions

## File Operations
Location: `backend/services/file_service.py`
- `get_extracted_file(file_id: str) -> Optional[ConfirmationFile]`
  - Purpose: Retrieves file that has completed text extraction
  - Used by: parse_text endpoint
- `update_parsed_file(file_id: str, parsed_result: Dict, model_id: str) -> None`
  - Purpose: Updates file with parsed results
  - Used by: parse_text endpoint

## PDF Processing
Location: `backend/services/pdf_service.py`
- `extract_text_from_pdf(file_id: UUID, file_path: str, file_name: str) -> Dict[str, Any]`
  - Purpose: Extracts text from PDF files
  - Used by: pdf_reader.py

## Status Management
Location: `backend/services/status_service.py`
- `create_status_history(file_id: UUID, previous_status: ProcessingStatus, new_status: ProcessingStatus, trigger_source: str, additional_data: Dict) -> FileStatusHistory`
  - Purpose: Creates and validates status transitions
  - Used by: All file processing endpoints

## Text Processing
Location: `backend/services/text_service.py`
- `parse_text_with_model(text: str, model_id: str) -> Dict[str, Any]`
  - Purpose: Parses text using AI models
  - Used by: parse_text endpoint 