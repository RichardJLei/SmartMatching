
# start backend server
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload


# DB management
alembic revision --autogenerate -m "description of changes"
alembic upgrade head

DB initialization:
python database/init_db.py
python database/init_db.py --reset