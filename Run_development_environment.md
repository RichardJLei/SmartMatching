
# start backend server
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload


DB management

# Initialize alembic in your project
alembic init migrations

# Generate a new migration
alembic revision --autogenerate -m "description of changes"

# Apply the migration to your database
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to a specific migration
alembic downgrade revision_id