# AI Work OS

Personal productivity tool để tự động hóa việc quản lý công việc từ văn bản thô.

**Triết lý**: Đơn giản, tiện lợi, gọn gàng - không phức tạp hóa!

## ✨ Tính năng

- **📝 Nhập tài liệu**: Paste email, meeting notes → tự động trích xuất tasks
- **🤖 Hỏi đáp thông minh**: RAG-based Q&A với context Tiếng Việt
- **✅ Quản lý task**: CRUD operations với state machine
- **🌐 UI đơn giản**: Single-page responsive interface
- **🚀 Ready to use**: Docker deployment trong 5 phút

## 🚀 Cài đặt Nhanh

### 1. Clone & Setup
```bash
git clone <repo-url>
cd text2tasks
cp .env.example .env
```

### 2. Cấu hình .env
```env
OPENAI_API_KEY=sk-your-openai-key-here
API_KEY=your-secure-api-key-here
```

### 3. Chạy với Docker (Khuyến nghị)
```bash
# Một lệnh là xong!
docker-compose up -d
```

Truy cập: http://localhost:8000

### 4. Hoặc chạy development
```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8000
```

## 📖 Cách sử dụng

### Web UI
1. Vào http://localhost:8000
2. Paste văn bản vào form "Ingest Document"
3. Xem tasks được tự động tạo
4. Chat với AI về nội dung documents

### API Examples

#### Tạo tasks từ văn bản
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "text": "Meeting 20/8: Hieu hoàn thành database schema trước thứ 6. Mai gửi report cho team.",
    "source": "meeting"
  }'
```

Response:
```json
{
  "document_id": "1",
  "summary": "Meeting 20/8: Hieu cần hoàn thiện database schema...",
  "actions": [
    {
      "title": "Hoàn thành database schema",
      "owner": "Hieu",
      "due": "2025-08-22",
      "status": "new"
    }
  ]
}
```

#### Hỏi đáp thông minh
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "question": "Database schema của Hieu thế nào rồi?"
  }'
```

#### Xem tất cả tasks
```bash
curl http://localhost:8000/tasks
```

#### Cập nhật task
```bash
curl -X PATCH http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "status": "in_progress",
    "owner": "Hieu"
  }'
```

## 🏗 Kiến trúc Hệ thống

### 🎨 **Frontend Architecture (Phase 1 - COMPLETED)**
```
🌐 React Frontend (Modern SPA)
├── 📱 Professional UI/UX
│   ├── Dark/Light theme
│   ├── Responsive design  
│   ├── Animated transitions
│   └── PWA capabilities
├── 🏗 Modern Stack
│   ├── React 18 + TypeScript
│   ├── Vite build system
│   ├── Tailwind CSS design system
│   └── Framer Motion animations
├── 🔧 State Management  
│   ├── Zustand (global state)
│   ├── React Query (server state)
│   └── Persistent storage
└── 🚀 Production Ready
    ├── Docker deployment
    ├── Nginx configuration
    ├── Service Worker (PWA)
    └── Performance optimized
```

### 🖥 **Backend Architecture**
```
🚀 FastAPI Backend
├── 🌐 API Endpoints
│   ├── /ingest         → Tạo tasks từ văn bản
│   ├── /ask            → Hỏi đáp với RAG
│   ├── /tasks          → CRUD tasks  
│   ├── /hierarchy      → Task hierarchy management
│   ├── /resources      → Document & resource library
│   ├── /status         → Tổng quan hệ thống
│   └── /healthz        → Health check
├── 🧠 AI Integration
│   ├── Vietnamese prompts
│   ├── RAG embeddings
│   ├── Smart extraction
│   └── Context-aware Q&A
└── 💾 Data Layer
    ├── SQLite Database
    ├── Vector embeddings
    └── Task hierarchy
```

### 🔄 **Full Stack Integration**
```
Frontend (Port 3000)    Backend (Port 8000)    
     │                       │
     ├─── HTTP/API ──────────┤
     ├─── WebSocket ─────────┤ (Future)
     └─── Proxy /api ────────┘
                            │
                    🧠 OpenAI APIs
                            │
                    💾 SQLite + Embeddings
```

### Task State Machine
```
new → in_progress → done
 ↓         ↓
blocked ←←←←
```

## 🔧 Environment Variables

| Variable | Default | Mô tả |
|----------|---------|-------|
| `OPENAI_API_KEY` | - | OpenAI API key (bắt buộc) |
| `API_KEY` | - | API key cho write operations |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API URL |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat model |
| `DB_URL` | `sqlite:///./app.db` | Database URL |
| `DEBUG` | `false` | Debug mode |

## 🐳 Docker Deployment

### Simple Docker Run
```bash
docker build -t ai-work-os .
docker run -d \
  --name ai-work-os \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e API_KEY=your-api-key \
  -v $(pwd)/data:/app/data \
  ai-work-os
```

### Docker Compose (Khuyến nghị)
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - API_KEY=${API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🧪 Testing

```bash
# Basic tests
pytest

# With coverage
pytest --cov=src

# Performance test
locust -f tests/locust/locustfile.py --host=http://localhost:8000
```

## 🛠 Development

### Code Structure
```
text2tasks/
├── 🖥 backend/
│   ├── src/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── database.py          # SQLite models
│   │   ├── llm_client.py        # AI integration
│   │   ├── schemas.py           # API schemas
│   │   └── routes/              # API endpoints
│   │       ├── health.py        # Health checks
│   │       ├── ingest.py        # Document processing
│   │       ├── ask.py           # Q&A functionality
│   │       ├── tasks.py         # Task management
│   │       ├── hierarchy.py     # Task hierarchy
│   │       ├── resources.py     # Resource management
│   │       └── status.py        # System status
│   ├── static/                  # Legacy HTML UI
│   └── tests/                   # Backend tests
├── 🎨 frontend/ (NEW!)
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── layout/         # Header, Sidebar, Layout
│   │   │   ├── common/         # Shared components
│   │   │   └── ui/             # Basic UI elements
│   │   ├── pages/              # Page components
│   │   ├── services/           # API client
│   │   ├── stores/             # State management
│   │   ├── hooks/              # Custom React hooks
│   │   ├── types/              # TypeScript definitions
│   │   └── utils/              # Helper functions
│   ├── public/                 # Static assets
│   ├── Dockerfile             # Frontend container
│   └── package.json           # Dependencies
└── 🐳 Docker/
    ├── Dockerfile             # Backend container
    ├── docker-compose.yml     # Full stack deployment
    └── nginx.conf             # Production web server
```

### Development Setup

#### Backend Development
```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run backend development server
python -m uvicorn src.main:app --reload --port 8000
```

#### Frontend Development (NEW!)
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies  
npm install

# Copy environment config
cp .env.example .env

# Start frontend development server
npm run dev
# Frontend will be available at http://localhost:3000
```

#### Full Stack Development
```bash
# Terminal 1: Backend
python -m uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend  
cd frontend && npm run dev

# Access:
# - Frontend: http://localhost:3000 (recommended)
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## 🔮 Roadmap

### ✅ Phase 1: Modern Frontend (COMPLETED)
- ✅ **Professional React Frontend**: TypeScript, Tailwind CSS, Modern UI/UX
- ✅ **State Management**: Zustand + React Query for optimal performance
- ✅ **Production Ready**: Docker deployment, PWA capabilities
- ✅ **Developer Experience**: Vite build system, Hot reload, Type safety

### ✅ Phase 2: Backend Optimization (COMPLETED) 
- ✅ **Core API functionality**: All endpoints working
- ✅ **Performance optimization**: Database indexes, connection pooling
- ✅ **Security hardening**: Rate limiting, input validation
- ✅ **Production deployment**: Docker optimization

### 🎯 Phase 3: Enhanced User Experience (Next)
- **Task Management**: Integrate existing TaskManagementApp.tsx
- **Real-time Features**: WebSocket for live updates
- **Advanced UI**: Virtual scrolling, drag & drop, animations
- **Performance**: Caching strategies, bundle optimization

### 🚀 Phase 4: Multi-Channel Convenience (Future)
- **Telegram Bot**: Commands + notifications
- **Email Integration**: Auto-extract from emails
- **Mobile Optimization**: Native app experience
- **Smart Features**: Auto-categorization, AI suggestions

### 🌟 Phase 5: Advanced Personal Features (Optional)
- Smart task prioritization
- Data export/sync
- Calendar integration
- Voice input

Chi tiết: [PROJECT_PLAN.md](PROJECT_PLAN.md)

## 💡 Tips & Tricks

### Vietnamese Prompts
- AI hiểu tiếng Việt tốt: "Tóm tắt cuộc họp hôm nay"
- Mixed language OK: "Meeting notes about database migration"

### Smart Task Detection
- Auto-detect người làm: "Hieu sẽ fix bug này"  
- Auto-detect deadline: "hoàn thành trước thứ 6"
- Auto-detect priority: "urgent", "quan trọng"

### Web UI Shortcuts
- `Ctrl+Enter`: Submit form
- `/` : Focus search
- `Esc`: Clear forms

## 🆘 Troubleshooting

### Common Issues

**Docker không start?**
```bash
# Check logs
docker-compose logs

# Rebuild
docker-compose down
docker-compose up --build
```

**API errors?**
- Kiểm tra OPENAI_API_KEY trong .env
- Verify API_KEY match between requests và .env

**Slow responses?**  
- Thêm Redis cache nếu cần
- Check OPENAI_BASE_URL nếu dùng proxy

**Vietnamese text issues?**
- Đảm bảo UTF-8 encoding
- Check database charset settings

## 🔒 Security

- API key authentication cho write operations
- Rate limiting built-in
- Input validation & sanitization  
- Security headers configured
- SQLite safe from injection attacks

## 📄 License

MIT License - Use freely for personal projects!

---

**🎯 Mục tiêu**: Personal productivity tool đơn giản, không phức tạp hóa!
**💪 Nguyên tắc**: Làm ít, làm tốt, dễ sử dụng hàng ngày.