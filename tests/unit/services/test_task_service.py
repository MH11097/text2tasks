"""Unit tests for TaskService"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime

from src.services.task_service import TaskService
from src.core.types import TaskStatus
from src.core.exceptions import TaskNotFoundException, ValidationException
from src.database import Task, Document

class TestTaskService:
    """Test TaskService functionality"""
    
    @pytest.fixture
    def task_service(self):
        """Create TaskService instance for testing"""
        return TaskService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        with patch('src.services.task_service.SessionLocal') as mock:
            session = MagicMock(spec=Session)
            mock.return_value.__aenter__.return_value = session
            mock.return_value.__aexit__.return_value = None
            yield session

class TestGetTasks:
    """Test get_tasks functionality"""
    
    @pytest.mark.asyncio
    async def test_get_tasks_all(self, task_service, mock_db_session):
        """Test getting all tasks"""
        # Mock tasks
        mock_tasks = [
            MagicMock(
                id=1, title="Task 1", status="new", due_date="2025-01-01",
                owner="John", source_doc_id=10, created_at=datetime.now(),
                updated_at=datetime.now(), blockers=[], project_hint="Project A"
            ),
            MagicMock(
                id=2, title="Task 2", status="in_progress", due_date=None,
                owner="Jane", source_doc_id=20, created_at=datetime.now(),
                updated_at=datetime.now(), blockers=["Blocked by dependency"], project_hint=None
            )
        ]
        
        query_mock = mock_db_session.query.return_value.join.return_value
        query_mock.order_by.return_value.limit.return_value.all.return_value = mock_tasks
        
        # Test
        results = await task_service.get_tasks()
        
        # Assertions
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["title"] == "Task 1"
        assert results[0]["status"] == "new"
        assert results[0]["due_date"] == "2025-01-01"
        assert results[0]["owner"] == "John"
        assert results[0]["source_doc_id"] == "10"
        
        assert results[1]["id"] == "2"
        assert results[1]["title"] == "Task 2"
        assert results[1]["status"] == "in_progress"
        assert results[1]["due_date"] is None
        assert results[1]["owner"] == "Jane"
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_status_filter(self, task_service, mock_db_session):
        """Test getting tasks with status filter"""
        query_mock = mock_db_session.query.return_value.join.return_value
        query_mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        await task_service.get_tasks(status_filter=TaskStatus.NEW)
        
        # Verify filter was applied
        query_mock.filter.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_owner_filter(self, task_service, mock_db_session):
        """Test getting tasks with owner filter"""
        query_mock = mock_db_session.query.return_value.join.return_value
        query_mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        await task_service.get_tasks(owner_filter="John")
        
        # Verify filter was applied
        query_mock.filter.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_source_type_filter(self, task_service, mock_db_session):
        """Test getting tasks with source type filter"""
        query_mock = mock_db_session.query.return_value.join.return_value
        query_mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        await task_service.get_tasks(source_type_filter="telegram")
        
        # Verify filter was applied
        query_mock.filter.assert_called_once()

class TestGetTaskById:
    """Test get_task_by_id functionality"""
    
    @pytest.mark.asyncio
    async def test_get_task_by_id_found(self, task_service, mock_db_session):
        """Test getting task by ID when found"""
        mock_task = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_task
        
        result = await task_service.get_task_by_id(123)
        
        assert result == mock_task
        mock_db_session.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_task_by_id_not_found(self, task_service, mock_db_session):
        """Test getting task by ID when not found"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await task_service.get_task_by_id(999)
        
        assert result is None

class TestUpdateTask:
    """Test update_task functionality"""
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, task_service, mock_db_session):
        """Test updating task status"""
        # Mock existing task
        mock_task = MagicMock()
        mock_task.id = 123
        mock_task.title = "Test Task"
        mock_task.status = "new"
        mock_task.owner = "John"
        mock_task.due_date = "2025-01-01"
        mock_task.source_doc_id = 10
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_task
        
        with patch('src.services.task_service.validate_task_status') as mock_validate, \
             patch('src.services.task_service.datetime') as mock_datetime:
            
            mock_validate.return_value = "in_progress"
            mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)
            
            result = await task_service.update_task(
                task_id=123,
                status="in_progress"
            )
        
        # Assertions
        assert result["id"] == "123"
        assert result["status"] == "in_progress"
        assert "status" in result["updated_fields"]
        
        # Verify task was updated
        assert mock_task.status == "in_progress"
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_task_owner(self, task_service, mock_db_session):
        """Test updating task owner"""
        mock_task = MagicMock()
        mock_task.id = 123
        mock_task.owner = "Old Owner"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_task
        
        with patch('src.services.task_service.validate_owner_input') as mock_validate, \
             patch('src.services.task_service.datetime') as mock_datetime:
            
            mock_validate.return_value = "New Owner"
            mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)
            
            result = await task_service.update_task(
                task_id=123,
                owner="New Owner"
            )
        
        assert "owner" in result["updated_fields"]
        assert mock_task.owner == "New Owner"
    
    @pytest.mark.asyncio
    async def test_update_task_due_date(self, task_service, mock_db_session):
        """Test updating task due date"""
        mock_task = MagicMock()
        mock_task.id = 123
        mock_task.due_date = "2025-01-01"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_task
        
        with patch('src.services.task_service.validate_date_input') as mock_validate, \
             patch('src.services.task_service.datetime') as mock_datetime:
            
            mock_validate.return_value = "2025-01-15"
            mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)
            
            result = await task_service.update_task(
                task_id=123,
                due_date="2025-01-15"
            )
        
        assert "due_date" in result["updated_fields"]
        assert mock_task.due_date == "2025-01-15"
    
    @pytest.mark.asyncio
    async def test_update_task_not_found(self, task_service, mock_db_session):
        """Test updating non-existent task"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(TaskNotFoundException):
            await task_service.update_task(task_id=999, status="done")
    
    @pytest.mark.asyncio
    async def test_update_task_multiple_fields(self, task_service, mock_db_session):
        """Test updating multiple task fields"""
        mock_task = MagicMock()
        mock_task.id = 123
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_task
        
        with patch('src.services.task_service.validate_task_status') as mock_validate_status, \
             patch('src.services.task_service.validate_owner_input') as mock_validate_owner, \
             patch('src.services.task_service.datetime') as mock_datetime:
            
            mock_validate_status.return_value = "done"
            mock_validate_owner.return_value = "Updated Owner"
            mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)
            
            result = await task_service.update_task(
                task_id=123,
                status="done",
                owner="Updated Owner"
            )
        
        assert "status" in result["updated_fields"]
        assert "owner" in result["updated_fields"]
        assert len(result["updated_fields"]) == 2

class TestTaskCounts:
    """Test get_task_counts_by_status functionality"""
    
    @pytest.mark.asyncio
    async def test_get_task_counts_by_status(self, task_service, mock_db_session):
        """Test getting task counts by status"""
        # Mock count queries for each status
        count_results = {"new": 5, "in_progress": 3, "blocked": 1, "done": 10}
        
        def mock_count(*args):
            # Extract the status from the filter call
            status = args[0].right.value  # Assuming this is how the status is extracted
            return count_results.get(status, 0)
        
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [5, 3, 1, 10]
        
        results = await task_service.get_task_counts_by_status()
        
        assert results["new"] == 5
        assert results["in_progress"] == 3
        assert results["blocked"] == 1
        assert results["done"] == 10

class TestTasksByOwner:
    """Test get_tasks_by_owner functionality"""
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_owner(self, task_service):
        """Test getting tasks by owner"""
        with patch.object(task_service, 'get_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [{"id": "1", "owner": "John"}]
            
            results = await task_service.get_tasks_by_owner("John", limit=25)
            
            mock_get_tasks.assert_called_once_with(owner_filter="John", limit=25)
            assert results == [{"id": "1", "owner": "John"}]

class TestOverdueTasks:
    """Test get_overdue_tasks functionality"""
    
    @pytest.mark.asyncio
    async def test_get_overdue_tasks(self, task_service, mock_db_session):
        """Test getting overdue tasks"""
        from datetime import date
        
        # Mock overdue tasks
        overdue_task = MagicMock()
        overdue_task.id = 1
        overdue_task.title = "Overdue Task"
        overdue_task.status = "in_progress"
        overdue_task.due_date = "2024-12-01"  # Past date
        overdue_task.owner = "John"
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [overdue_task]
        
        with patch('src.services.task_service.date') as mock_date:
            mock_date.today.return_value = date(2025, 1, 15)
            mock_date.fromisoformat.return_value = date(2024, 12, 1)
            
            results = await task_service.get_overdue_tasks()
        
        assert len(results) == 1
        assert results[0]["id"] == "1"
        assert results[0]["title"] == "Overdue Task"
        assert results[0]["days_overdue"] == 45  # 2025-01-15 - 2024-12-01