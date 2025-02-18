# Project Structure Overview

## Backend Structure

### Root Directory (`/backend`)
- `main.py`: FastAPI application entry point, configures routes and middleware.
- `requirements.txt`: Python package dependencies.
- `pytest.ini`: Pytest configuration file for running tests.

### API Layer (`/backend/api`)
- `__init__.py`: Initializes the api package.
- `pdf_reader.py`: API endpoints for PDF processing and text parsing.
- `auth.py`: API endpoints for user authentication and authorization.
- `routes/`: Subdirectory containing route definitions.
    - `__init__.py`: Initializes the routes package.
    - `pdf.py`: PDF-related routes (e.g., `/extract-text`, `/parse-text`).
    - `auth.py`: Authentication routes (e.g., `/login`, `/register`).
    - `health.py`: Health check endpoint for monitoring the API.

### Configuration (`/backend/config`)
- `.env`: Environment variables and secrets (API keys, database URLs).
- `model_config.py`: Pydantic models for configuring AI models.
- `database_config.py`: Database connection settings.
- `app_config.py`: General application settings.

### Database (`/backend/database`)
- `database.py`: Database connection and session management using SQLAlchemy.
- `models/`: Subdirectory containing database models.
    - `__init__.py`: Initializes the models package.
    - `user.py`: SQLAlchemy model for the `users` table.
    - `pdf_file.py`: SQLAlchemy model for the `pdf_files` table.
- `migrations/`: Alembic migrations for database schema management.

### Services (`/backend/services`)
- `file_service.py`: Service for handling file operations (upload, storage, etc.).
- `model_service.py`: Service for integrating with AI models (Nvidia, DeepSeek).
- `auth_service.py`: Service for handling authentication logic.
- `pdf_service.py`: Service for handling PDF processing logic.

### Utilities (`/backend/utils`)
- `pdf_processor.py`: Utilities for PDF file processing (text extraction, etc.).
- `text_parser.py`: Utilities for parsing extracted text using AI models.
- `logger.py`: Logging configuration for the backend.
- `rules/`: Subdirectory containing parsing rules.
    - `banking_rules.py`: Parsing rules specific to banking documents.
    - `matching_rules.py`: General pattern matching rules.

### Tests (`/backend/tests`)
- `__init__.py`: Initializes the tests package.
- `conftest.py`: Pytest configuration file for setting up test environment.
- `test_pdf_reader.py`: Tests for the PDF reader API endpoints.
- `test_auth.py`: Tests for the authentication API endpoints.

## Frontend Structure

### Root Directory (`/frontend`)
- `package.json`: npm package file, lists dependencies and scripts.
- `vite.config.ts`: Configuration file for the Vite build tool.
- `tsconfig.json`: TypeScript configuration file.

### Source Files (`/frontend/src`)
- `main.tsx`: Entry point for the React application.
- `App.tsx`: Root component of the application.
- `components/`: Directory containing reusable React components.
- `pages/`: Directory containing page-level components.
- `services/`: Directory containing API service functions.
- `utils/`: Directory containing utility functions.
- `assets/`: Directory containing static assets (images, fonts, etc.).

### Configuration (`/frontend/config`)
- `.env`: Environment variables for the frontend.
- `config.ts`: Configuration file for the frontend application.

## Project Documentation (`/_docs`)
- `README.md`: Project overview and setup instructions.
- `Project-style.md`: Coding style guidelines and standards.
- `Project-structure.md`: This document, describing project organization.
- `API-docs.md`: Documentation for the backend API endpoints.

## Key Features

1. **PDF Processing**
    - Secure file upload and storage.
    - Text extraction and OCR.
    - Content parsing and validation.

2. **AI Model Integration**
    - Support for multiple AI models (Nvidia, DeepSeek).
    - Configurable model pipeline.
    - Error handling and fallbacks.

3. **Data Management**
    - PostgreSQL database for persistent storage.
    - File tracking and versioning.
    - Result caching and storage.

4. **Security**
    - Authentication and authorization.
    - Input validation to prevent attacks.
    - Rate limiting to protect against abuse.

5. **Monitoring**
    - Logging and tracing for debugging and auditing.
    - Performance metrics for identifying bottlenecks.
    - Error tracking for identifying and resolving issues.
