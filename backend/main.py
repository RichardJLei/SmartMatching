from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from api.routes import pdf
from api import pdf_reader
from api.routes.confirmation_files import extract_text, parse_text
from api.routes.matching_units import extract_matching_units

class SensitiveDataFilter(logging.Filter):
    """Filter out sensitive and verbose data from logs"""
    def filter(self, record):
        # Skip long messages containing request/response data
        if 'Request options' in str(record.msg):
            return False
        if 'HTTP Response' in str(record.msg):
            return False
        if 'messages' in str(record.msg):
            return False
        return True

# Configure logging with filter
logging.getLogger("openai").setLevel(logging.WARNING)  # Reduce OpenAI logging
logging.getLogger("httpx").setLevel(logging.WARNING)   # Reduce HTTP client logging
logging.getLogger("httpcore").setLevel(logging.WARNING)  # Reduce HTTP core logging

# Configure root logger
logger = logging.getLogger(__name__)
logger.addFilter(SensitiveDataFilter())

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with detailed logging
logger.debug("Registering pdf_reader router...")
app.include_router(pdf_reader.router, prefix="/api")
logger.debug("Registering pdf router...")
app.include_router(pdf.router, prefix="/api", tags=["pdf"])
logger.debug("Registering extract_text router...")
app.include_router(
    extract_text.router,
    prefix="/api",
    tags=["confirmation_files"]
)
logger.debug("Registering parse_text router...")
app.include_router(
    parse_text.router,
    prefix="/api",
    tags=["confirmation_files"]
)
logger.debug("Registering extract_matching_units router...")
app.include_router(
    extract_matching_units.router,
    prefix="/api",
    tags=["matching_units"]
)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    logger.info("Registered routes:")
    for route in app.routes:
        logger.info(f"Route: {route.path}, Methods: {route.methods}, Name: {route.name}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 