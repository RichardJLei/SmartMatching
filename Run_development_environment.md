
# start backend server
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload


# DB management
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
