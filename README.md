# AI Work OS

Hệ thống AI Work OS tối giản để tự động hóa việc quản lý công việc từ văn bản thô.

## Tính năng

- **Nhập tài liệu**: Xử lý email, ghi chú cuộc họp, văn bản và trích xuất tự động các action items
- **Hỏi đáp thông minh**: RAG-based Q&A với embeddings và cosine similarity
- **Quản lý task**: CRUD operations với state machine validation
- **UI đơn giản**: Single-page interface để tương tác với hệ thống

## Cài đặt

### Yêu cầu
- Python 3.8+
- OpenAI API key (hoặc API tương thích)

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình environment

Sao chép `.env.example` thành `.env` và cập nhật các giá trị:

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
API_KEY=your-secure-api-key-here
```

### 3. Chạy ứng dụng

```bash
# Development
python -m uvicorn src.main:app --reload --port 8000

# Production  
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Truy cập: http://localhost:8000

## Docker Deployment

### 1. Sử dụng Docker Compose (Khuyến nghị)

```bash
# Tạo file .env với các biến môi trường
cp .env.example .env

# Chạy với Docker Compose
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng services
docker-compose down
```

### 2. Sử dụng Docker trực tiếp

```bash
# Build image
docker build -t ai-work-os .

# Run container
docker run -d \
  --name ai-work-os \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e API_KEY=your-api-key \
  -v $(pwd)/data:/app/data \
  ai-work-os
```

## API Documentation

### Authentication
Các endpoint ghi (POST, PATCH) yêu cầu header `X-API-Key`.

### Endpoints

#### Health Check
```bash
curl http://localhost:8000/healthz
```

#### Ingest Document
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "text": "2025-08-16 Meeting: Hieu finalize schema by Wed; blocker: prod access.",
    "source": "meeting"
  }'
```

Response:
```json
{
  "document_id": "1",
  "summary": "Cuộc họp ngày 16/8: Hieu cần hoàn thiện schema trước thứ Tư...",
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
```

#### Ask Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "question": "Trạng thái schema như thế nào?",
    "top_k": 6
  }'
```

Response:
```json
{
  "answer": "Hieu đang phụ trách hoàn thiện database schema, hạn chót thứ Tư nhưng bị block do thiếu quyền prod.",
  "refs": ["1"],
  "suggested_next_steps": [
    "Xin quyền truy cập production",
    "Kiểm tra timeline backup"
  ]
}
```

#### List Tasks
```bash
# All tasks
curl http://localhost:8000/tasks

# Filter by status
curl "http://localhost:8000/tasks?status=in_progress"

# Filter by owner
curl "http://localhost:8000/tasks?owner=Hieu"
```

#### Update Task
```bash
curl -X PATCH http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "status": "in_progress",
    "owner": "Hieu",
    "due_date": "2025-08-25"
  }'
```

#### System Status
```bash
curl http://localhost:8000/status
```

Response:
```json
{
  "summary": "Đang có 2 task cần xử lý. 1 task mới, 1 đang thực hiện. Nên bắt đầu với các task mới.",
  "counts": {
    "new": 1,
    "in_progress": 1, 
    "blocked": 0,
    "done": 3
  }
}
```

## Task State Machine

Các chuyển đổi trạng thái hợp lệ:
- `new` → `in_progress` hoặc `blocked`
- `in_progress` → `done` hoặc `blocked`
- `blocked` → `in_progress`
- `done` → (không chuyển được)

## Testing

```bash
# Chạy tests
pytest

# Với coverage
pytest --cov=src

# Chạy specific test
pytest tests/test_acceptance.py::TestHealthCheck::test_healthz
```

## Kiến trúc

```
src/
├── main.py              # FastAPI app chính
├── config.py            # Cấu hình environment  
├── database.py          # SQLAlchemy models
├── llm_client.py        # OpenAI client + prompts
├── schemas.py           # Pydantic models
└── routes/
    ├── health.py        # Health check
    ├── ingest.py        # Document ingestion
    ├── ask.py           # Q&A with RAG
    ├── tasks.py         # Task management
    └── status.py        # System status
```

### Database Models
- **Document**: Lưu văn bản gốc và tóm tắt
- **Embedding**: Vector embeddings cho RAG
- **Task**: Action items với state machine

### LLM Integration
- **Extraction**: Prompts tiếng Việt cho tóm tắt + action items
- **Embeddings**: Vector generation cho semantic search
- **Q&A**: Context-aware với fallback messages

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API base URL |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat model |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `API_KEY` | - | API key cho authentication (required) |
| `DB_URL` | `sqlite:///./app.db` | Database URL |
| `RAG_TOP_K` | `6` | Số lượng documents cho RAG |
| `ALLOWED_ORIGIN` | `http://localhost:8000` | CORS origin |
| `DEBUG` | `false` | Debug mode |

## Development

### Roadmap
Xem [PROJECT_PLAN.md](PROJECT_PLAN.md) để biết kế hoạch phát triển chi tiết.

### Contributing
1. Fork repository
2. Tạo feature branch
3. Commit changes với tests
4. Tạo Pull Request

## License

MIT License