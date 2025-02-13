from fastapi import FastAPI
from api import pdf_reader

app = FastAPI()
app.include_router(pdf_reader.router) 