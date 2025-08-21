"""Database models for the Text2Tasks application"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    source = Column(String(50), nullable=False, index=True)  # email|meeting|note|other
    source_type = Column(String(20), default="web", index=True)  # web|telegram|email
    source_id = Column(String(100), index=True)  # telegram_user_id|email_address|session_id
    doc_metadata = Column(JSON, default=dict)  # platform-specific data
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="source_document", cascade="all, delete-orphan")

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
    source_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_document = relationship("Document", back_populates="tasks")

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