from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from api.routes import pdf
from api import pdf_reader

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level for more detail
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
app.include_router(pdf_reader.router, prefix="/api")  # Add prefix here
logger.debug("Registering pdf router...")
app.include_router(pdf.router, prefix="/api", tags=["pdf"])

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