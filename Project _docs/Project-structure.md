# Project Structure Overview

## Backend Structure

### Root Directory (`/backend`)
- `main.py` - FastAPI application entry point, configures routes and middleware
- `requirements.txt` - Python package dependencies

### API Layer (`/backend/api`)
- `__init__.py` - Package initialization
- `pdf_reader.py` - API endpoints for PDF processing and text parsing
  - `/extract-text` - Extract text from PDF files
  - `/parse-text` - Parse extracted text using AI models
  - `/test-model-connection` - Test AI model connectivity

### Configuration (`/backend/config`)
- `.env` - Environment variables and secrets
  - Database configuration
  - Model API keys and settings
  - Service configurations
- `model_config.py` - Model settings using Pydantic
- `database_config.py` - Database connection settings

### Database (`/backend/database`)
- `database.py` - Database connection and session management
- `models.py` - SQLAlchemy ORM models
- `init_db.py` - Database initialization and schema management

### Services (`/backend/services`)
- `file_service.py` - File operations and database interactions
  - File status tracking
  - Parsing result management
- `model_service.py` - AI model integration
  - Base model service interface
  - Nvidia Deepseek implementation
  - DeepSeek Chat implementation
  - Model factory for service creation

### Utilities (`/backend/utils`)
- `pdf_processor.py` - PDF file processing utilities
- `text_parser.py` - Text parsing coordination
- `ConvertBankingConfoInstruction.rules` - Parsing rules for banking confirmations

### Storage
- `received_files/` - Temporary storage for uploaded files
- `bank_parsed_text.json` - Sample parsed text output

## Frontend Structure

### Root Directory (`/frontend`)
- `config/` - Frontend configuration
  - `.env` - Frontend environment variables

## Project Documentation
- `README.md` - Project overview and setup instructions
- `Project-styple.md` - Coding style guidelines and standards
- `Project-structure.md` - This document, describing project organization

## Key Features
1. **PDF Processing**
   - File upload and storage
   - Text extraction
   - Content parsing

2. **AI Model Integration**
   - Multiple model support (Nvidia, DeepSeek)
   - Extensible model service architecture
   - Standardized parsing rules

3. **Data Management**
   - PostgreSQL database
   - File tracking
   - Parsing results storage

4. **API Endpoints**
   - RESTful API design
   - Error handling
   - Status tracking

5. **Configuration Management**
   - Environment-based configuration
   - Secure credentials handling
   - Service settings management
