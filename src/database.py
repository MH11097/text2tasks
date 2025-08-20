from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, Table, Boolean, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from typing import List, Optional
from .config import settings

engine = create_engine(
    settings.db_url, 
    echo=settings.debug,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Many-to-many association table for documents and tasks
document_tasks = Table(
    'document_tasks',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', String(100)),
    Column('inherited', Boolean, default=False),
    UniqueConstraint('document_id', 'task_id'),
    Index('idx_doc_tasks_doc', 'document_id'),
    Index('idx_doc_tasks_task', 'task_id')
)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    source = Column(String(50), nullable=False, index=True)  # email|meeting|note|other
    source_type = Column(String(20), default="web", index=True)  # web|telegram|email
    source_id = Column(String(100), index=True)  # telegram_user_id|email_address|session_id
    doc_metadata = Column(JSON, default=dict)  # platform-specific data (renamed from metadata)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Assignment status for resource management
    assignment_status = Column(String(20), default="unassigned", index=True)  # unassigned|assigned|archived
    
    # Relationships
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="source_document", cascade="all, delete-orphan")
    
    # Many-to-many with tasks for resource assignment
    assigned_tasks = relationship("Task", secondary="document_tasks", back_populates="assigned_documents")

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    vector = Column(JSON, nullable=False)  # Store as JSON list of floats
    
    # Relationships
    document = relationship("Document", back_populates="embeddings")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(20), default="new", index=True)  # new|in_progress|blocked|done
    due_date = Column(String(10), index=True)  # YYYY-MM-DD format
    owner = Column(String(100), index=True)
    blockers = Column(JSON, default=list)  # List of blocker strings
    project_hint = Column(String(100))
    source_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # Made nullable for hierarchy
    
    # Hierarchy fields
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    task_level = Column(Integer, default=0, index=True)  # 0=root, 1=level1, etc.
    task_path = Column(String(500), index=True)  # "PROJ-001/DEV-001/API-001"
    task_code = Column(String(20), unique=True, index=True)  # Short identifier
    
    # Enhanced tracking fields
    description = Column(Text)  # Current status description
    progress_percentage = Column(Integer, default=0)  # 0-100
    priority = Column(String(20), default="medium", index=True)  # low|medium|high|urgent
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_document = relationship("Document", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id], backref="children")
    
    # Many-to-many with documents
    assigned_documents = relationship("Document", secondary="document_tasks", back_populates="assigned_tasks")

class MessageQueue(Base):
    __tablename__ = "message_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(20), nullable=False, index=True)  # telegram|email|web
    message_data = Column(JSON, nullable=False)  # Raw message payload
    status = Column(String(20), default="pending", index=True)  # pending|processing|completed|failed
    error_message = Column(Text)  # Error details if failed
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime)

def create_tables():
    Base.metadata.create_all(bind=engine)
    
def add_indexes():
    """Add performance indexes for multi-source queries"""
    from sqlalchemy import text
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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()