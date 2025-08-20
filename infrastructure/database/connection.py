"""Database connection and session management"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.config.settings import settings
from .models import Base

engine = create_engine(
    settings.db_url, 
    echo=settings.debug,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    
def add_indexes():
    """Add performance indexes for multi-source queries"""
    with engine.connect() as conn:
        try:
            # Multi-source document indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_source_type_created ON documents(source_type, created_at)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_source_id_type ON documents(source_id, source_type)"))
            
            # Message queue indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_message_queue_status_created ON message_queue(status, created_at)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_message_queue_source_status ON message_queue(source_type, status)"))
            
            conn.commit()
        except Exception as e:
            print(f"Index creation warning: {e}")

def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db_session():
    """Async dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()