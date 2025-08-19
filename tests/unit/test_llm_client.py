"""Unit tests for LLMClient"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import numpy as np

from src.llm_client import LLMClient, cosine_similarity

class TestLLMClient:
    """Test LLMClient functionality"""
    
    @pytest.fixture
    def llm_client(self):
        """Create LLMClient instance for testing"""
        with patch('src.llm_client.settings') as mock_settings:
            mock_settings.openai_base_url = "https://api.openai.com/v1"
            mock_settings.openai_api_key = "test-api-key"
            mock_settings.openai_chat_model = "gpt-4o-mini"
            mock_settings.openai_embedding_model = "text-embedding-3-small"
            yield LLMClient()

class TestExtractSummaryAndActions:
    """Test extract_summary_and_actions method"""
    
    @pytest.mark.asyncio
    async def test_extract_summary_and_actions_success(self, llm_client):
        """Test successful extraction"""
        # Mock HTTP response
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "summary": "Meeting về database schema và deployment",
                            "actions": [
                                {
                                    "title": "Hoàn thiện database schema",
                                    "owner": "John",
                                    "due": "2025-01-15",
                                    "blockers": [],
                                    "project_hint": "Database project"
                                },
                                {
                                    "title": "Deploy to staging",
                                    "owner": null,
                                    "due": null,
                                    "blockers": ["Schema completion"],
                                    "project_hint": null
                                }
                            ]
                        })
                    }
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await llm_client.extract_summary_and_actions("Meeting notes about database")
        
        # Assertions
        assert result["summary"] == "Meeting về database schema và deployment"
        assert len(result["actions"]) == 2
        assert result["actions"][0]["title"] == "Hoàn thiện database schema"
        assert result["actions"][0]["owner"] == "John"
        assert result["actions"][0]["due"] == "2025-01-15"
        assert result["actions"][1]["owner"] is None
    
    @pytest.mark.asyncio
    async def test_extract_summary_and_actions_api_error(self, llm_client):
        """Test API error handling"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception) as exc_info:
                await llm_client.extract_summary_and_actions("Test text")
            
            assert "LLM API error: 500" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_summary_and_actions_json_decode_error(self, llm_client):
        """Test handling of invalid JSON response"""
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Invalid JSON response from LLM"
                    }
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await llm_client.extract_summary_and_actions("Test text")
        
        # Should return fallback response
        assert result["summary"] == "Không thể trích xuất tóm tắt từ văn bản này."
        assert result["actions"] == []
    
    @pytest.mark.asyncio
    async def test_extract_summary_and_actions_request_format(self, llm_client):
        """Test correct request format"""
        mock_response_data = {
            "choices": [{"message": {"content": '{"summary": "Test", "actions": []}'}}]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await llm_client.extract_summary_and_actions("Test input")
            
            # Verify request format
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            
            assert kwargs["json"]["model"] == "gpt-4o-mini"
            assert kwargs["json"]["temperature"] == 0.1
            assert kwargs["json"]["max_tokens"] == 1000
            assert len(kwargs["json"]["messages"]) == 2
            assert "Test input" in kwargs["json"]["messages"][1]["content"]

class TestGenerateEmbeddings:
    """Test generate_embeddings method"""
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, llm_client):
        """Test successful embedding generation"""
        mock_response_data = {
            "data": [
                {
                    "embedding": [0.1, 0.2, 0.3, -0.1, -0.2]
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await llm_client.generate_embeddings("Test text for embedding")
        
        assert result == [0.1, 0.2, 0.3, -0.1, -0.2]
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_api_error(self, llm_client):
        """Test embedding API error"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception) as exc_info:
                await llm_client.generate_embeddings("Test text")
            
            assert "Embedding API error: 400" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_request_format(self, llm_client):
        """Test correct embedding request format"""
        mock_response_data = {"data": [{"embedding": [0.1, 0.2]}]}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await llm_client.generate_embeddings("Test input text")
            
            # Verify request format
            args, kwargs = mock_post.call_args
            assert kwargs["json"]["model"] == "text-embedding-3-small"
            assert kwargs["json"]["input"] == "Test input text"

class TestAnswerQuestion:
    """Test answer_question method"""
    
    @pytest.mark.asyncio
    async def test_answer_question_success(self, llm_client):
        """Test successful question answering"""
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "answer": "Database schema đang được thiết kế bởi John, dự kiến hoàn thành vào 15/1.",
                            "suggested_next_steps": ["Kiểm tra với John về tiến độ", "Review schema draft"]
                        })
                    }
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await llm_client.answer_question(
                "Database schema thế nào rồi?",
                "Context: Meeting notes about database project..."
            )
        
        assert "Database schema đang được thiết kế" in result["answer"]
        assert len(result["suggested_next_steps"]) == 2
        assert "Kiểm tra với John" in result["suggested_next_steps"][0]
    
    @pytest.mark.asyncio
    async def test_answer_question_json_decode_error(self, llm_client):
        """Test handling of invalid JSON in answer"""
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Not valid JSON response"
                    }
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await llm_client.answer_question("Test question", "Test context")
        
        # Should return fallback response
        assert result["answer"] == "Chưa đủ thông tin trong hệ thống để trả lời câu hỏi này."
        assert "Thêm thông tin liên quan" in result["suggested_next_steps"]
    
    @pytest.mark.asyncio
    async def test_answer_question_request_format(self, llm_client):
        """Test correct answer request format"""
        mock_response_data = {
            "choices": [{"message": {"content": '{"answer": "Test", "suggested_next_steps": []}'}}]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await llm_client.answer_question("Test question", "Test context")
            
            # Verify request format
            args, kwargs = mock_post.call_args
            assert kwargs["json"]["temperature"] == 0.3
            assert kwargs["json"]["max_tokens"] == 500
            assert "Test question" in kwargs["json"]["messages"][1]["content"]
            assert "Test context" in kwargs["json"]["messages"][1]["content"]

class TestCosineSimilarity:
    """Test cosine_similarity utility function"""
    
    def test_cosine_similarity_identical_vectors(self):
        """Test similarity of identical vectors"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert abs(similarity - 1.0) < 1e-10  # Should be exactly 1.0
    
    def test_cosine_similarity_orthogonal_vectors(self):
        """Test similarity of orthogonal vectors"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert abs(similarity - 0.0) < 1e-10  # Should be exactly 0.0
    
    def test_cosine_similarity_opposite_vectors(self):
        """Test similarity of opposite vectors"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert abs(similarity - (-1.0)) < 1e-10  # Should be exactly -1.0
    
    def test_cosine_similarity_partial_match(self):
        """Test similarity of partially matching vectors"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 1.0, 0.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        # Should be 1/sqrt(2) ≈ 0.707
        expected = 1.0 / np.sqrt(2)
        assert abs(similarity - expected) < 1e-10
    
    def test_cosine_similarity_zero_vector(self):
        """Test similarity with zero vector"""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert similarity == 0.0  # Should return 0 for zero norm
    
    def test_cosine_similarity_both_zero_vectors(self):
        """Test similarity of two zero vectors"""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [0.0, 0.0, 0.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert similarity == 0.0  # Should return 0 when both norms are 0
    
    def test_cosine_similarity_different_dimensions(self):
        """Test that function works with different vector sizes"""
        vec1 = [0.1] * 1536  # Standard embedding dimension
        vec2 = [0.2] * 1536
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert 0.99 < similarity < 1.01  # Should be close to 1.0
    
    def test_cosine_similarity_numpy_conversion(self):
        """Test that function correctly converts to numpy arrays"""
        vec1 = [1, 2, 3]  # Python list
        vec2 = np.array([2, 4, 6])  # NumPy array
        
        similarity = cosine_similarity(vec1, vec2)
        
        # vec2 = 2 * vec1, so similarity should be 1.0
        assert abs(similarity - 1.0) < 1e-10