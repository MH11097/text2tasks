#!/usr/bin/env python3
"""
Create test data for demonstration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SessionLocal, Document, Task
from src.services.task_hierarchy_service import TaskHierarchyService
from src.services.resource_assignment_service import ResourceAssignmentService
from datetime import datetime, timedelta

def create_test_data():
    """Create sample tasks and documents for testing"""
    db = SessionLocal()
    
    try:
        print("Creating test data...")
        
        # Check if data already exists
        existing_tasks = db.query(Task).count()
        if existing_tasks > 0:
            print(f"Test data already exists ({existing_tasks} tasks). Skipping creation.")
            return
        
        hierarchy_service = TaskHierarchyService(db)
        resource_service = ResourceAssignmentService(db)
        
        # Create sample documents first
        documents = [
            Document(
                text="Website redesign project requirements: Need to create modern, responsive design with improved user experience. Focus on mobile-first approach and accessibility.",
                source="email",
                source_type="web",
                summary="Website redesign requirements and specifications",
                assignment_status="unassigned"
            ),
            Document(
                text="Meeting notes: Discussed API architecture for the new backend system. Need to implement REST endpoints with proper authentication and rate limiting.",
                source="meeting",
                source_type="web", 
                summary="Backend API architecture meeting notes",
                assignment_status="unassigned"
            ),
            Document(
                text="User testing feedback: Users reported difficulty navigating the current interface. Suggestions include better menu structure and search functionality.",
                source="note",
                source_type="web",
                summary="User testing feedback and suggestions",
                assignment_status="unassigned"
            ),
            Document(
                text="Development guidelines: All code should follow PEP 8 standards. Include unit tests for new features. Use type hints where appropriate.",
                source="other",
                source_type="web",
                summary="Development coding standards and guidelines",
                assignment_status="unassigned"
            ),
            Document(
                text="Database migration plan: Upgrade from SQLite to PostgreSQL for production. Need to handle data migration and update connection strings.",
                source="note",
                source_type="web",
                summary="Database migration planning document",
                assignment_status="unassigned"
            )
        ]
        
        for doc in documents:
            db.add(doc)
        db.commit()
        
        # Refresh to get IDs
        for doc in documents:
            db.refresh(doc)
        
        print(f"✅ Created {len(documents)} sample documents")
        
        # Create hierarchical tasks
        root_task = hierarchy_service.create_task(
            title="Website Redesign Project",
            task_code="PROJ-001",
            description="Complete website redesign with modern UI/UX and improved backend",
            priority="high",
            owner="Project Manager",
            due_date="2024-03-15"
        )
        
        # Design tasks
        design_parent = hierarchy_service.create_task(
            title="UI/UX Design Phase",
            parent_task_id=root_task.id,
            task_code="DESIGN-001",
            description="Create wireframes, mockups, and design system",
            priority="high",
            owner="UI Designer"
        )
        
        wireframes_task = hierarchy_service.create_task(
            title="Create Wireframes",
            parent_task_id=design_parent.id,
            task_code="DESIGN-001-1",
            description="Mobile and desktop wireframes for all pages",
            priority="medium",
            owner="UI Designer"
        )
        
        mockups_task = hierarchy_service.create_task(
            title="Design Mockups",
            parent_task_id=design_parent.id,
            task_code="DESIGN-001-2",
            description="High-fidelity mockups based on wireframes",
            priority="medium",
            owner="UI Designer"
        )
        
        # Development tasks
        dev_parent = hierarchy_service.create_task(
            title="Frontend Development",
            parent_task_id=root_task.id,
            task_code="DEV-001",
            description="Implement responsive frontend with React",
            priority="high",
            owner="Frontend Developer"
        )
        
        components_task = hierarchy_service.create_task(
            title="React Components",
            parent_task_id=dev_parent.id,
            task_code="DEV-001-1",
            description="Build reusable UI components",
            priority="medium",
            owner="Frontend Developer"
        )
        
        api_task = hierarchy_service.create_task(
            title="API Integration",
            parent_task_id=dev_parent.id,
            task_code="DEV-001-2",
            description="Integrate with backend APIs",
            priority="medium",
            owner="Frontend Developer"
        )
        
        # Backend tasks
        backend_parent = hierarchy_service.create_task(
            title="Backend Development",
            parent_task_id=root_task.id,
            task_code="BACK-001",
            description="Develop REST API and database layer",
            priority="high",
            owner="Backend Developer"
        )
        
        print("✅ Created hierarchical task structure")
        
        # Assign documents to tasks
        assignments = [
            # Website requirements to root project
            (documents[0].id, [root_task.id]),
            # API notes to backend tasks
            (documents[1].id, [backend_parent.id, api_task.id]),
            # User feedback to design tasks
            (documents[2].id, [design_parent.id, wireframes_task.id]),
            # Development guidelines to all dev tasks
            (documents[3].id, [dev_parent.id, components_task.id, backend_parent.id]),
            # Database migration to backend
            (documents[4].id, [backend_parent.id])
        ]
        
        for doc_id, task_ids in assignments:
            resource_service.assign_resource_to_tasks(
                resource_id=doc_id,
                task_ids=task_ids,
                assigned_by="system"
            )
        
        print("✅ Assigned resources to tasks")
        
        # Update some task progress
        hierarchy_service.update_task_progress(wireframes_task.id, 90)
        hierarchy_service.update_task_progress(mockups_task.id, 60)
        hierarchy_service.update_task_progress(components_task.id, 75)
        
        # Update task statuses
        wireframes_task.status = "in_progress"
        mockups_task.status = "in_progress" 
        components_task.status = "in_progress"
        api_task.status = "blocked"
        backend_parent.status = "in_progress"
        
        db.commit()
        
        print("✅ Updated task progress and statuses")
        print("\n🎉 Test data created successfully!")
        print("\nCreated tasks:")
        print(f"  - {root_task.task_code}: {root_task.title}")
        print(f"  - {design_parent.task_code}: {design_parent.title}")
        print(f"    - {wireframes_task.task_code}: {wireframes_task.title}")
        print(f"    - {mockups_task.task_code}: {mockups_task.title}")
        print(f"  - {dev_parent.task_code}: {dev_parent.title}")
        print(f"    - {components_task.task_code}: {components_task.title}")
        print(f"    - {api_task.task_code}: {api_task.title}")
        print(f"  - {backend_parent.task_code}: {backend_parent.title}")
        print(f"\nCreated {len(documents)} documents with resource assignments")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()