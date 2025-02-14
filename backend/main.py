from fastapi import FastAPI
from api.pdf_reader import router as pdf_router

app = FastAPI()

# Include the router
app.include_router(pdf_router) 