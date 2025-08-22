# Text2Tasks Documentation

## System Overview
Text2Tasks: AI Work OS - Clean Architecture system for converting unstructured text into actionable tasks.

## Current Status
✅ **Phase 1 Complete**: Backend API Extensions  
🔄 **Phase 2 Active**: Frontend Development

## Core APIs

### Tasks
- `GET /api/v1/tasks` - List with filtering/sorting
- `POST /api/v1/tasks` - Create with document linking
- `GET /api/v1/tasks/{id}/documents` - Get linked docs
- `POST /api/v1/tasks/{id}/documents` - Link docs

### Documents  
- `GET /api/v1/documents` - List with pagination
- `POST /api/v1/documents` - Create document
- `GET /api/v1/documents/{id}/tasks` - Get linked tasks
- `POST /api/v1/documents/{id}/tasks` - Link tasks

### Features
- Bidirectional Task ↔ Document relationships
- Enhanced filtering: status, priority, owner, created_by
- Sorting: created_at, updated_at, title, priority
- Junction table with metadata tracking

## Tech Stack
- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: React 18 + TypeScript + Vite
- Architecture: Clean Architecture pattern

## Quick Start
```bash
python -m app.main  # Start backend
open http://localhost:8000/docs  # API docs
```

## File Structure
```
docs/
├── README.md                    # This overview
├── architecture/ARCHITECTURE.md # System architecture
├── planning/PROJECT_PLAN.md     # Implementation roadmap
└── api/*.md                     # API documentation
```