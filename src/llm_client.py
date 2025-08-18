import httpx
import json
import numpy as np
from typing import List, Dict, Any
from .config import settings

class LLMClient:
    def __init__(self):
        self.base_url = settings.openai_base_url
        self.api_key = settings.openai_api_key
        self.chat_model = settings.openai_chat_model
        self.embedding_model = settings.openai_embedding_model
        
    async def extract_summary_and_actions(self, text: str) -> Dict[str, Any]:
        """Extract summary and action items from text using Vietnamese prompts"""
        
        system_prompt = """Bạn là trình trích xuất cấu trúc công việc. Luôn trả JSON hợp lệ. Không bịa thông tin. Nếu không rõ owner/due → để null. Tóm tắt ≤ 120 từ, khách quan, không ý kiến."""
        
        user_prompt = f"""Nội dung:

{text}

ASSISTANT (JSON)

{{
  "summary": "… <=120 từ …",
  "actions": [
    {{
      "title": "…ngắn gọn, động từ mở đầu…",
      "owner": null,
      "due": null,
      "blockers": [],
      "project_hint": null
    }}
  ]
}}

Quy tắc:
- actions có thể rỗng nếu không có.
- due định dạng YYYY-MM-DD nếu xuất hiện trong văn bản.
- Không suy diễn chủ quan; mọi thông tin phải đến từ văn bản gốc."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.chat_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "summary": "Không thể trích xuất tóm tắt từ văn bản này.",
                    "actions": []
                }
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.embedding_model,
                    "input": text
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Embedding API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["data"][0]["embedding"]
    
    async def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """Answer question based on context using Vietnamese prompts"""
        
        system_prompt = """Bạn trả lời dựa trên CONTEXT. Nếu thiếu dữ liệu, nói "Chưa đủ thông tin trong hệ thống". Trả lời ngắn gọn, kèm 1–2 "Next Steps" thực tế. Không bịa."""
        
        user_prompt = f"""CONTEXT

{context}

USER
Câu hỏi: {question}

ASSISTANT

{{
  "answer": "…ngắn gọn, chính xác, nếu thiếu thì nói rõ…",
  "suggested_next_steps": ["…", "…"]
}}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.chat_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "answer": "Chưa đủ thông tin trong hệ thống để trả lời câu hỏi này.",
                    "suggested_next_steps": ["Thêm thông tin liên quan", "Kiểm tra lại câu hỏi"]
                }

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    a_np = np.array(a)
    b_np = np.array(b)
    
    dot_product = np.dot(a_np, b_np)
    norm_a = np.linalg.norm(a_np)
    norm_b = np.linalg.norm(b_np)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)