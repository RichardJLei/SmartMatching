import logging
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add backend directory to Python path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Import models after setting up path
from database.models import Base, PartyCode

# Load environment variables
load_dotenv(os.path.join(backend_dir, 'config/.env'))

def get_sync_engine():
    """Create and return synchronous database engine for initialization."""
    # Convert async DB_URL to sync URL for initialization
    db_url = os.getenv('DB_URL')
    if not db_url:
        raise ValueError("DB_URL environment variable is not set")
    
    # Convert asyncpg to psycopg2 for sync operations
    sync_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    return create_engine(sync_url)

def init_database():
    """Initialize the database with tables and initial data."""
    engine = get_sync_engine()
    
    try:
        # Create pgcrypto extension
        with engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
            conn.commit()
            logger.info("✅ pgcrypto extension created/verified")

        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("✅ Database tables created successfully")
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Add initial party codes if needed
            initial_parties = [
                {
                    'party_code': 'BANK001',
                    'party_name': 'Example Bank',
                    'party_role': 'bank',
                    'is_active': True
                },
                {
                    'party_code': 'CORP001',
                    'party_name': 'Example Corporate',
                    'party_role': 'corporate',
                    'is_active': True
                }
            ]
            
            # Check if parties already exist
            for party_data in initial_parties:
                existing_party = session.query(PartyCode).filter_by(
                    party_code=party_data['party_code']
                ).first()
                
                if not existing_party:
                    party = PartyCode(**party_data)
                    session.add(party)
                    logger.info(f"✅ Added initial party: {party_data['party_code']}")
            
            session.commit()
            logger.info("✅ Initial data loaded successfully")
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {str(e)}")
        raise

def reset_database():
    """Reset the database by dropping all tables and recreating them."""
    engine = get_sync_engine()
    
    try:
        # Drop all tables
        Base.metadata.drop_all(engine)
        logger.info("✅ All tables dropped successfully")
        
        # Recreate tables and initial data
        init_database()
        logger.info("✅ Database reset completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error resetting database: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--reset':
            logger.info("🔄 Resetting database...")
            reset_database()
        else:
            logger.info("🔄 Initializing database...")
            init_database()
    except Exception as e:
        logger.error(f"Failed to initialize/reset database: {str(e)}")
        sys.exit(1) 