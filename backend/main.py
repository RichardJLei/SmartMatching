from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from api.routes import pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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

# Include routers
app.include_router(pdf.router, prefix="/api", tags=["pdf"])

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    # Log all registered routes
    for route in app.routes:
        logger.info(f"Registered route: {route.path}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 