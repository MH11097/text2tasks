"""Database models for the Text2Tasks application"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional

Base = declarative_base()

# Association table for many-to-many relationship between tasks and documents
task_documents = Table(
    'task_documents',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('created_by', String(100)),
    # Ensure unique task-document pairs
    schema=None
)

# Add indexes for performance
from sqlalchemy import Index
Index('idx_task_documents_task_id', task_documents.c.task_id)
Index('idx_task_documents_document_id', task_documents.c.document_id)
Index('idx_task_documents_unique', task_documents.c.task_id, task_documents.c.document_id, unique=True)

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
    # Many-to-many relationship with tasks
    linked_tasks = relationship("Task", secondary="task_documents", back_populates="linked_documents")

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
    description = Column(Text)  # Added description field
    status = Column(String(20), default="new", index=True)  # new|in_progress|blocked|done
    priority = Column(String(10), default="medium", index=True)  # low|medium|high|urgent
    due_date = Column(String(10), index=True)  # YYYY-MM-DD format
    owner = Column(String(100), index=True)
    blockers = Column(JSON, default=list)  # List of blocker strings
    project_hint = Column(String(100))
    source_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # Made nullable for manually created tasks
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))  # Track who created the task
    
    # Relationships
    source_document = relationship("Document", back_populates="tasks")
    # Many-to-many relationship with documents
    linked_documents = relationship("Document", secondary="task_documents", back_populates="linked_tasks")
    # Task dependencies
    dependencies = relationship("TaskDependency", foreign_keys="TaskDependency.dependent_task_id", back_populates="dependent_task")
    dependent_tasks = relationship("TaskDependency", foreign_keys="TaskDependency.prerequisite_task_id", back_populates="prerequisite_task")

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    dependent_task_id = Column(Integer, ForeignKey("tasks.id", ondelete='CASCADE'), nullable=False, index=True)  # Task that depends on another
    prerequisite_task_id = Column(Integer, ForeignKey("tasks.id", ondelete='CASCADE'), nullable=False, index=True)  # Task that must be completed first
    dependency_type = Column(String(20), default="blocks", index=True)  # blocks|related|subtask
    description = Column(String(255))  # Optional description of the dependency
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(100))
    
    # Relationships
    dependent_task = relationship("Task", foreign_keys=[dependent_task_id], back_populates="dependencies")
    prerequisite_task = relationship("Task", foreign_keys=[prerequisite_task_id], back_populates="dependent_tasks")

# Indexes for task dependencies
Index('idx_task_dependencies_dependent', TaskDependency.dependent_task_id)
Index('idx_task_dependencies_prerequisite', TaskDependency.prerequisite_task_id)
Index('idx_task_dependencies_type', TaskDependency.dependency_type)
Index('idx_task_dependencies_unique', TaskDependency.dependent_task_id, TaskDependency.prerequisite_task_id, unique=True)

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