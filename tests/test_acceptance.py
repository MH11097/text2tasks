import pytest
from unittest.mock import patch, AsyncMock


class TestHealthCheck:
    def test_healthz(self, client):
        """Test health check endpoint"""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestIngestionFlow:
    @patch('src.llm_client.LLMClient.extract_summary_and_actions')
    @patch('src.llm_client.LLMClient.generate_embeddings')
    def test_ingest_and_ask_flow(self, mock_embeddings, mock_extract, client, headers):
        """Test full workflow: ingest document → extract → ask question"""
        
        # Mock LLM responses
        mock_extract.return_value = {
            "summary": "Cuộc họp ngày 16/8: Hieu cần hoàn thiện schema trước thứ Tư, bị block do thiếu quyền prod.",
            "actions": [
                {
                    "title": "Hoàn thiện database schema",
                    "owner": "Hieu",
                    "due": "2025-08-20",
                    "blockers": ["Thiếu quyền truy cập production"],
                    "project_hint": "Database migration"
                }
            ]
        }
        
        mock_embeddings.return_value = [0.1] * 1536  # Mock embedding vector
        
        # Test ingest
        doc_data = {
            "text": "2025-08-16 Meeting: Hieu finalize schema by Wed; blocker: prod access.",
            "source": "meeting"
        }
        
        response = client.post("/ingest", headers=headers, json=doc_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "document_id" in result
        assert "summary" in result
        assert "actions" in result
        assert len(result["actions"]) == 1
        assert result["actions"][0]["title"] == "Hoàn thiện database schema"
        assert result["actions"][0]["owner"] == "Hieu"
        
        document_id = result["document_id"]
        
        # Test ask with mocked LLM response for Q&A
        with patch('src.llm_client.LLMClient.answer_question') as mock_answer:
            mock_answer.return_value = {
                "answer": "Hieu đang phụ trách hoàn thiện database schema, hạn chót thứ Tư nhưng bị block do thiếu quyền prod.",
                "suggested_next_steps": ["Xin quyền truy cập production", "Kiểm tra timeline backup"]
            }
            
            ask_data = {"question": "Trạng thái schema như thế nào?"}
            response = client.post("/ask", headers=headers, json=ask_data)
            assert response.status_code == 200
            
            result = response.json()
            assert "answer" in result
            assert "refs" in result
            assert "suggested_next_steps" in result
            assert document_id in result["refs"]


class TestTaskManagement:
    @patch('src.llm_client.LLMClient.extract_summary_and_actions')
    @patch('src.llm_client.LLMClient.generate_embeddings')
    def test_task_workflow(self, mock_embeddings, mock_extract, client, headers):
        """Test task creation and management"""
        
        # Mock responses
        mock_extract.return_value = {
            "summary": "Test summary",
            "actions": [
                {"title": "Test task", "owner": "John", "due": "2025-08-25", "blockers": [], "project_hint": None}
            ]
        }
        mock_embeddings.return_value = [0.1] * 1536
        
        # Create document with task
        doc_data = {"text": "Create test task for John due 2025-08-25", "source": "note"}
        response = client.post("/ingest", headers=headers, json=doc_data)
        assert response.status_code == 200
        
        # Get tasks
        response = client.get("/tasks")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        
        task = tasks[0]
        assert task["title"] == "Test task"
        assert task["status"] == "new"
        assert task["owner"] == "John"
        
        # Update task status
        task_id = task["id"]
        update_data = {"status": "in_progress"}
        response = client.patch(f"/tasks/{task_id}", headers=headers, json=update_data)
        assert response.status_code == 200
        
        # Verify update
        response = client.get("/tasks")
        tasks = response.json()
        updated_task = next(t for t in tasks if t["id"] == task_id)
        assert updated_task["status"] == "in_progress"
        
        # Test invalid status transition
        update_data = {"status": "done"}  # Should be valid: in_progress -> done
        response = client.patch(f"/tasks/{task_id}", headers=headers, json=update_data)
        assert response.status_code == 200
        
        # Test invalid transition (done -> new should fail)
        update_data = {"status": "new"}
        response = client.patch(f"/tasks/{task_id}", headers=headers, json=update_data)
        assert response.status_code == 400


class TestFiltering:
    @patch('src.llm_client.LLMClient.extract_summary_and_actions')
    @patch('src.llm_client.LLMClient.generate_embeddings')
    def test_task_filtering(self, mock_embeddings, mock_extract, client, headers):
        """Test task filtering by status and owner"""
        
        # Mock responses for multiple tasks
        mock_extract.return_value = {
            "summary": "Test summary",
            "actions": [
                {"title": "Task 1", "owner": "Alice", "due": None, "blockers": [], "project_hint": None},
                {"title": "Task 2", "owner": "Bob", "due": None, "blockers": [], "project_hint": None}
            ]
        }
        mock_embeddings.return_value = [0.1] * 1536
        
        # Create document with multiple tasks
        doc_data = {"text": "Alice should do task 1, Bob should do task 2", "source": "note"}
        response = client.post("/ingest", headers=headers, json=doc_data)
        assert response.status_code == 200
        
        # Filter by status
        response = client.get("/tasks?status=new")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 2
        assert all(task["status"] == "new" for task in tasks)
        
        # Filter by owner
        response = client.get("/tasks?owner=Alice")
        assert response.status_code == 200
        tasks = response.json()
        alice_tasks = [task for task in tasks if task["owner"] == "Alice"]
        assert len(alice_tasks) >= 1


class TestStatusEndpoint:
    def test_status_empty_system(self, client):
        """Test status endpoint with no tasks"""
        response = client.get("/status")
        assert response.status_code == 200
        
        result = response.json()
        assert "summary" in result
        assert "counts" in result
        assert result["counts"]["new"] == 0
        assert result["counts"]["in_progress"] == 0
        assert result["counts"]["blocked"] == 0
        assert result["counts"]["done"] == 0


class TestErrorHandling:
    def test_ingest_without_api_key(self, client):
        """Test ingest endpoint without API key"""
        doc_data = {"text": "Test", "source": "note"}
        response = client.post("/ingest", json=doc_data)
        assert response.status_code == 401
    
    def test_ingest_invalid_source(self, client, headers):
        """Test ingest with invalid source"""
        doc_data = {"text": "Test", "source": "invalid"}
        response = client.post("/ingest", headers=headers, json=doc_data)
        assert response.status_code == 422
    
    def test_ask_insufficient_context(self, client, headers):
        """Test ask endpoint when no documents exist"""
        ask_data = {"question": "What is the status?"}
        response = client.post("/ask", headers=headers, json=ask_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "Chưa đủ thông tin" in result["answer"]
    
    def test_update_nonexistent_task(self, client, headers):
        """Test updating a task that doesn't exist"""
        update_data = {"status": "done"}
        response = client.patch("/tasks/99999", headers=headers, json=update_data)
        assert response.status_code == 404


class TestDataValidation:
    def test_task_date_validation(self, client, headers):
        """Test task due date validation"""
        # This would need a task to exist first, so we'll create one
        with patch('src.llm_client.LLMClient.extract_summary_and_actions') as mock_extract, \
             patch('src.llm_client.LLMClient.generate_embeddings') as mock_embeddings:
            
            mock_extract.return_value = {
                "summary": "Test",
                "actions": [{"title": "Test task", "owner": None, "due": None, "blockers": [], "project_hint": None}]
            }
            mock_embeddings.return_value = [0.1] * 1536
            
            # Create task
            doc_data = {"text": "Test task", "source": "note"}
            response = client.post("/ingest", headers=headers, json=doc_data)
            
            # Get task ID
            response = client.get("/tasks")
            task_id = response.json()[0]["id"]
            
            # Test invalid date format
            update_data = {"due_date": "invalid-date"}
            response = client.patch(f"/tasks/{task_id}", headers=headers, json=update_data)
            assert response.status_code == 422
            
            # Test valid date format
            update_data = {"due_date": "2025-12-31"}
            response = client.patch(f"/tasks/{task_id}", headers=headers, json=update_data)
            assert response.status_code == 200