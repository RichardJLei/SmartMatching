# AI Workflow Documentation

This document describes the workflow of AI processing in our system.

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Endpoint
    participant Parser as TextParser
    participant Factory as ModelFactory
    participant Service as ModelService
    participant AI as AI Model (DeepSeek/Nvidia)
    participant DB as Database

    Client->>API: POST /api/parse-text
    Note over Client,API: {file_id, model_id}
    API->>DB: Get extracted text
    DB-->>API: Return file data
    API->>Parser: parse_with_model(text, model_id)
    Parser->>Factory: get_model_service(model_id)
    Factory-->>Parser: Return model service instance
    Note over Service: Load parsing instructions
    Note over Service: from ConvertBankingConfoInstruction.rules
    Parser->>Service: parse_text(text)
    Service->>AI: Send prompt
    Note over Service,AI: System prompt:<br/>1. You are a financial document parser<br/>2. Custom parsing instructions<br/>3. Return JSON only
    AI-->>Service: Raw JSON response
    Service->>Service: Clean & validate JSON
    Note over Service: 1. Extract JSON from markdown<br/>2. Parse & validate structure<br/>3. Add model metadata
    Service-->>Parser: Return result
    Note over Service,Parser: {<br/> "parsed_content": {...},<br/> "model_info": {<br/> "provider": "nvidia/openai",<br/> "model": "model_name"<br/> }<br/>}
    Parser-->>API: Return parsed result
    API->>DB: Save parsed result
    Note over API,DB: Remove original text<br/>Add timestamp & metadata
    API-->>Client: Return response
    Note over API,Client: {<br/> "data": {<br/> "id": "file_id",<br/> "status": "completed",<br/> "success": true,<br/> "model": {...},<br/> "result": {...},<br/> "metadata": {...}<br/> },<br/> "error": null<br/>}
```

## Key Components

1. **Text Parser**
   - Manages the parsing workflow
   - Interfaces with model services
   - Handles initial error checking

2. **Model Factory**
   - Creates appropriate model service instances
   - Supports multiple model types (DeepSeek, Nvidia)
   - Enables easy addition of new models

3. **Model Services**
   - Handles model-specific implementations
   - Loads parsing instructions
   - Manages prompts and response processing
   - Ensures consistent output format

4. **AI Models**
   - DeepSeek Chat
   - Nvidia Deepseek
   - Both accessed via OpenAI-compatible API

## Data Flow

1. **Input**
   - File ID and model selection
   - Extracted text from PDF
   - Parsing instructions

2. **Processing**
   - System prompt construction
   - AI model processing
   - JSON extraction and validation
   - Metadata addition

3. **Output**
   - Structured JSON data
   - Model information
   - Processing metadata
   - Status and error handling

## Error Handling

- Input validation at each step
- Comprehensive error logging
- Structured error responses
- Transaction rollback for database operations