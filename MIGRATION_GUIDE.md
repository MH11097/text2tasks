# Migration Guide: Clean Architecture Implementation

## What Changed

### Before (Monolithic Structure)
```
src/
├── database.py        # Models + Connection + Session management
├── llm_client.py     # LLM integration
├── services/         # Business logic mixed with data access
├── routes/           # API endpoints
├── config.py         # Configuration
└── core/            # Types and exceptions
```

### After (Clean Architecture)
```
domain/              # Business logic (no external dependencies)
├── entities/        # Domain entities and types
├── repositories/    # Abstract interfaces
└── services/        # Pure business logic

infrastructure/      # External concerns
├── database/        # Data persistence
├── external/        # Third-party integrations
├── security/        # Security implementations
└── logging/         # Logging configuration

interfaces/          # User interfaces
├── api/            # REST API
├── telegram/       # Bot interface
└── cli/           # Command line

shared/             # Common utilities
└── config/         # Application settings

app/               # Application composition
├── main.py        # Entry point
└── dependencies.py # Dependency injection
```

## Key Changes Made

### 1. Database Layer Separation

**Before:**
```python
# src/database.py - Everything mixed together
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.db_url)
SessionLocal = sessionmaker(bind=engine)

class Document(Base):
    # Model definition
    pass

def get_db():
    # Session management
    pass
```

**After:**
```python
# infrastructure/database/models.py - Pure models
class Document(Base):
    # Only model definition
    pass

# infrastructure/database/connection.py - Only connection logic
engine = create_engine(settings.db_url)
SessionLocal = sessionmaker(bind=engine)

# infrastructure/database/repositories/ - Data access implementation
class DocumentRepository(IDocumentRepository):
    # Implements domain interface
    pass
```

### 2. Service Layer Clean-up

**Before:**
```python
# src/services/document_service.py - Mixed concerns
from ..database import Document, SessionLocal
from ..llm_client import LLMClient

class DocumentService:
    def __init__(self):
        self.llm_client = LLMClient()  # Direct dependency
    
    async def process(self, text):
        # Direct database access
        async with SessionLocal() as db:
            # Business logic mixed with data access
```

**After:**
```python
# domain/services/document_service.py - Pure business logic
class DocumentService:
    def __init__(self, document_repository: IDocumentRepository, llm_client: LLMClient):
        self.repository = document_repository  # Dependency injection
        self.llm_client = llm_client
    
    async def process(self, text):
        # Pure business logic
        document = DocumentEntity(text=text)
        return await self.repository.create(document)
```

### 3. API Routes Refactoring

**Before:**
```python
# src/routes/ingest.py - Tightly coupled
from ..services.document_service import DocumentService

router = APIRouter()
service = DocumentService()  # Direct instantiation
```

**After:**
```python
# interfaces/api/v1/ingest.py - Dependency injection
from app.dependencies import container

router = APIRouter()

@router.post("/ingest")
async def ingest(request: IngestRequest):
    service = DocumentService(
        container.document_repository,
        container.llm_client
    )
    return await service.process_document(request.text)
```

## Impact on Existing Code

### Import Changes Required

**Old imports:**
```python
from src.database import Document, get_db
from src.services.document_service import DocumentService
from src.core.types import SourceType
from src.llm_client import LLMClient
```

**New imports:**
```python
from infrastructure.database.models import Document
from infrastructure.database.connection import get_db
from domain.services.document_service import DocumentService
from domain.entities.types import SourceType
from infrastructure.external.openai_client import LLMClient
```

### Service Instantiation Changes

**Old way:**
```python
# Services created their own dependencies
service = DocumentService()  # Self-contained
result = await service.process_document(text)
```

**New way:**
```python
# Dependencies injected
from app.dependencies import container

service = DocumentService(
    document_repository=container.document_repository,
    llm_client=container.llm_client
)
result = await service.process_document(text)
```

## Breaking Changes

### 1. Service Constructors
All service classes now require dependencies to be injected:

```python
# OLD
class DocumentService:
    def __init__(self):
        self.llm_client = LLMClient()

# NEW  
class DocumentService:
    def __init__(self, document_repository: IDocumentRepository, llm_client: LLMClient):
        self.repository = document_repository
        self.llm_client = llm_client
```

### 2. Direct Database Access
Direct database imports and session creation no longer work:

```python
# OLD - Don't do this anymore
from src.database import SessionLocal, Document
async with SessionLocal() as db:
    doc = db.query(Document).first()

# NEW - Use repository pattern
document = await document_repository.get_by_id(1)
```

### 3. Configuration Imports
Configuration moved to shared layer:

```python
# OLD
from src.config import settings

# NEW
from shared.config.settings import settings
```

## Testing Changes

### 1. Unit Testing Domain Services

**Before - Hard to test:**
```python
# Service created its own dependencies
service = DocumentService()  # Can't mock LLMClient
```

**After - Easy to mock:**
```python
# Mock dependencies
mock_repository = Mock(spec=IDocumentRepository)
mock_llm_client = Mock(spec=LLMClient)

service = DocumentService(mock_repository, mock_llm_client)
# Easy to test business logic in isolation
```

### 2. Repository Testing

**New capability:**
```python
# Test repository implementations separately
repository = DocumentRepository()
mock_db_session = Mock()
# Test data access logic
```

## Migration Steps for Developers

### 1. Update Imports
- Replace all `src.` imports with new layer structure
- Update relative imports in moved files

### 2. Update Service Usage
- Replace direct service instantiation with dependency injection
- Use `app.dependencies.container` for getting configured services

### 3. Update Tests
- Mock repository interfaces instead of database sessions
- Inject mocked dependencies into services
- Test each layer separately

### 4. Update Configuration
- Update any hardcoded paths to configuration
- Use `shared.config.settings` for all config access

## Benefits Realized

### 1. **Improved Testability**
- Easy to mock external dependencies
- Domain logic testable in isolation
- Clear test boundaries

### 2. **Better Separation of Concerns**
- Business logic separated from technical details
- Database changes don't affect business logic
- API changes don't affect domain

### 3. **Enhanced Maintainability**
- Clear structure for new features
- Easy to locate and modify code
- Reduced coupling between components

### 4. **Future-Proof Architecture**
- Can swap implementations without changing business logic
- Supports microservice extraction
- Easy to add new interfaces

## Troubleshooting Common Issues

### Issue: Import Errors
```python
# Error: ModuleNotFoundError: No module named 'src.database'
# Solution: Update to new import paths
from infrastructure.database.models import Document
```

### Issue: Service Instantiation Errors
```python
# Error: Missing required arguments for service constructor
# Solution: Use dependency injection
from app.dependencies import container
service = DocumentService(container.document_repository, container.llm_client)
```

### Issue: Test Failures
```python
# Error: Can't mock external dependencies
# Solution: Mock repository interfaces
mock_repo = Mock(spec=IDocumentRepository)
service = DocumentService(mock_repo, mock_llm_client)
```