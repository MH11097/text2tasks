#!/usr/bin/env python3
"""
Migration script for Task Hierarchy and Resource Assignment features
- Adds hierarchy fields to tasks table
- Creates document_tasks many-to-many table
- Adds assignment_status to documents table
- Migrates existing data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from src.database import engine, SessionLocal
from src.logging_config import get_logger

logger = get_logger(__name__)
import uuid

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if column already exists in table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def check_table_exists(table_name: str) -> bool:
    """Check if table exists"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def migrate_tasks_table():
    """Add hierarchy fields to tasks table"""
    logger.info("Migrating tasks table...")
    
    with engine.connect() as conn:
        # Add hierarchy columns if they don't exist
        hierarchy_columns = [
            ("parent_task_id", "INTEGER"),
            ("task_level", "INTEGER DEFAULT 0"),
            ("task_path", "VARCHAR(500)"),
            ("task_code", "VARCHAR(20)"),
            ("description", "TEXT"),
            ("progress_percentage", "INTEGER DEFAULT 0"),
            ("priority", "VARCHAR(20) DEFAULT 'medium'")
        ]
        
        for col_name, col_def in hierarchy_columns:
            if not check_column_exists("tasks", col_name):
                logger.info(f"Adding column {col_name} to tasks table")
                conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_def}"))
            else:
                logger.info(f"Column {col_name} already exists in tasks table")
        
        # Make source_doc_id nullable
        logger.info("Making source_doc_id nullable...")
        try:
            # SQLite doesn't support ALTER COLUMN, so we need to check if it's already nullable
            conn.execute(text("UPDATE tasks SET source_doc_id = NULL WHERE source_doc_id = 0"))
        except Exception as e:
            logger.warning(f"Could not update source_doc_id: {e}")
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_level ON tasks(task_level)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_path ON tasks(task_path)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_code ON tasks(task_code)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)"
        ]
        
        for idx_sql in indexes:
            logger.info(f"Creating index: {idx_sql}")
            conn.execute(text(idx_sql))
        
        conn.commit()
        logger.info("Tasks table migration completed")

def migrate_documents_table():
    """Add assignment_status to documents table"""
    logger.info("Migrating documents table...")
    
    with engine.connect() as conn:
        # Add assignment_status column if it doesn't exist
        if not check_column_exists("documents", "assignment_status"):
            logger.info("Adding assignment_status column to documents table")
            conn.execute(text("ALTER TABLE documents ADD COLUMN assignment_status VARCHAR(20) DEFAULT 'unassigned'"))
            
            # Create index
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_docs_assignment ON documents(assignment_status)"))
        else:
            logger.info("assignment_status column already exists in documents table")
        
        conn.commit()
        logger.info("Documents table migration completed")

def create_document_tasks_table():
    """Create document_tasks many-to-many table"""
    logger.info("Creating document_tasks table...")
    
    if check_table_exists("document_tasks"):
        logger.info("document_tasks table already exists")
        return
    
    with engine.connect() as conn:
        create_table_sql = """
        CREATE TABLE document_tasks (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assigned_by VARCHAR(100),
            inherited BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            UNIQUE(document_id, task_id)
        )
        """
        
        conn.execute(text(create_table_sql))
        
        # Create indexes
        indexes = [
            "CREATE INDEX idx_doc_tasks_doc ON document_tasks(document_id)",
            "CREATE INDEX idx_doc_tasks_task ON document_tasks(task_id)"
        ]
        
        for idx_sql in indexes:
            conn.execute(text(idx_sql))
        
        conn.commit()
        logger.info("document_tasks table created successfully")

def migrate_existing_data():
    """Migrate existing task-document relationships to new structure"""
    logger.info("Migrating existing data...")
    
    db = SessionLocal()
    try:
        with db.begin():
            # Generate task_codes for existing tasks
            result = db.execute(text("SELECT id, title FROM tasks WHERE task_code IS NULL"))
            tasks = result.fetchall()
            
            for task in tasks:
                # Generate a simple task code based on ID
                task_code = f"TASK-{task.id:03d}"
                
                db.execute(
                    text("UPDATE tasks SET task_code = :code, task_level = 0 WHERE id = :id"),
                    {"code": task_code, "id": task.id}
                )
                logger.info(f"Generated task_code {task_code} for task {task.id}")
            
            # Create document_tasks relationships for existing tasks
            # Each task already has a source_doc_id, so we'll create the many-to-many relationship
            result = db.execute(text("SELECT id, source_doc_id FROM tasks WHERE source_doc_id IS NOT NULL"))
            task_docs = result.fetchall()
            
            for task_doc in task_docs:
                # Check if relationship already exists
                existing = db.execute(
                    text("SELECT 1 FROM document_tasks WHERE document_id = :doc_id AND task_id = :task_id"),
                    {"doc_id": task_doc.source_doc_id, "task_id": task_doc.id}
                ).fetchone()
                
                if not existing:
                    db.execute(
                        text("""
                        INSERT INTO document_tasks (document_id, task_id, assigned_by, inherited)
                        VALUES (:doc_id, :task_id, 'migration', FALSE)
                        """),
                        {"doc_id": task_doc.source_doc_id, "task_id": task_doc.id}
                    )
                    logger.info(f"Created document_tasks relationship: doc {task_doc.source_doc_id} -> task {task_doc.id}")
            
            # Update assignment_status for documents that have tasks
            db.execute(text("""
            UPDATE documents 
            SET assignment_status = 'assigned' 
            WHERE id IN (
                SELECT DISTINCT document_id 
                FROM document_tasks
            )
            """))
            
            logger.info("Data migration completed successfully")
            
    except Exception as e:
        logger.error(f"Error during data migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def validate_migration():
    """Validate the migration was successful"""
    logger.info("Validating migration...")
    
    db = SessionLocal()
    try:
        # Check tasks table structure
        result = db.execute(text("SELECT COUNT(*) FROM tasks WHERE task_code IS NOT NULL")).fetchone()
        logger.info(f"Tasks with task_code: {result[0]}")
        
        # Check document_tasks table
        result = db.execute(text("SELECT COUNT(*) FROM document_tasks")).fetchone()
        logger.info(f"Document-task relationships: {result[0]}")
        
        # Check documents assignment status
        result = db.execute(text("SELECT assignment_status, COUNT(*) FROM documents GROUP BY assignment_status")).fetchall()
        for status, count in result:
            logger.info(f"Documents with status '{status}': {count}")
        
        logger.info("Migration validation completed")
        
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        raise
    finally:
        db.close()

def main():
    """Run the complete migration"""
    logger.info("Starting hierarchy migration...")
    
    try:
        # Step 1: Migrate tasks table
        migrate_tasks_table()
        
        # Step 2: Migrate documents table
        migrate_documents_table()
        
        # Step 3: Create document_tasks table
        create_document_tasks_table()
        
        # Step 4: Migrate existing data
        migrate_existing_data()
        
        # Step 5: Validate migration
        validate_migration()
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()