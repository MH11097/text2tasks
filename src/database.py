from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from typing import List, Optional
from .config import settings

engine = create_engine(settings.db_url, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)  # email|meeting|note|other
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="source_document", cascade="all, delete-orphan")

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    vector = Column(JSON, nullable=False)  # Store as JSON list of floats
    
    # Relationships
    document = relationship("Document", back_populates="embeddings")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(20), default="new")  # new|in_progress|blocked|done
    due_date = Column(String(10))  # YYYY-MM-DD format
    owner = Column(String(100))
    blockers = Column(JSON, default=list)  # List of blocker strings
    project_hint = Column(String(100))
    source_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_document = relationship("Document", back_populates="tasks")

def create_tables():
    Base.metadata.create_all(bind=engine)

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