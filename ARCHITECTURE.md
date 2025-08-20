# Clean Architecture Implementation

## Overview

This project now follows Clean Architecture principles, with clear separation of concerns across multiple layers.

## Architecture Layers

### 1. Domain Layer (`domain/`)
The innermost layer containing business logic, entities, and interfaces.

```
domain/
├── entities/          # Domain entities and value objects
│   ├── document.py   # Document entity
│   ├── task.py       # Task entity
│   ├── types.py      # Common types and enums
│   └── exceptions.py # Domain-specific exceptions
├── repositories/     # Abstract repository interfaces
│   ├── document_repository.py
│   └── task_repository.py
└── services/        # Domain services (business logic)
    ├── document_service.py
    ├── task_service.py
    └── background_service.py
```

**Key Principles:**
- No dependencies on external frameworks
- Contains pure business logic
- Defines interfaces for data access

### 2. Infrastructure Layer (`infrastructure/`)
Handles external concerns like databases, APIs, and third-party services.

```
infrastructure/
├── database/        # Database implementations
│   ├── models.py    # SQLAlchemy models
│   ├── connection.py # Database configuration
│   └── repositories/ # Concrete repository implementations
├── external/        # External service integrations
│   ├── openai_client.py # LLM client
│   └── telegram/    # Telegram bot integration
├── security/        # Security implementations
│   └── security.py  # Input validation and security
└── logging/         # Logging configuration
    └── config.py
```

**Key Features:**
- Implements domain repository interfaces
- Handles database connections and transactions
- Manages external API communications

### 3. Interface Layer (`interfaces/`)
Handles communication with external actors (users, systems).

```
interfaces/
├── api/            # REST API endpoints
│   ├── v1/         # API version 1
│   └── schemas/    # Request/response schemas
├── telegram/       # Telegram bot interface
└── cli/           # Command-line interface
```

**Responsibilities:**
- HTTP request/response handling
- Input validation and serialization
- API versioning

### 4. Shared Layer (`shared/`)
Common utilities and configurations used across layers.

```
shared/
├── config/         # Configuration management
│   └── settings.py # Application settings
└── utils/         # Shared utilities
```

### 5. Application Layer (`app/`)
Application composition and dependency wiring.

```
app/
├── main.py         # Application entry point
└── dependencies.py # Dependency injection setup
```

## Dependency Flow

```
Interfaces → Domain ← Infrastructure
     ↓         ↑
   Shared ← Application
```

**Key Rules:**
1. **Domain** has no dependencies on other layers
2. **Infrastructure** depends only on Domain interfaces
3. **Interfaces** depend on Domain and use Infrastructure through DI
4. **Application** orchestrates all layers through dependency injection

## Benefits Achieved

### 1. **Separation of Concerns**
- Business logic isolated in Domain layer
- Technical details contained in Infrastructure
- User interfaces separated from business logic

### 2. **Testability**
- Easy to mock external dependencies
- Domain logic can be tested in isolation
- Repository interfaces enable test doubles

### 3. **Maintainability**
- Changes to external services don't affect business logic
- Clear boundaries between layers
- Single responsibility principle enforced

### 4. **Flexibility**
- Can swap database implementations without changing business logic
- Can add new interfaces (GraphQL, gRPC) without touching domain
- External service changes are isolated to Infrastructure layer

### 5. **Scalability**
- Clear structure for adding new features
- Easy to identify where new code should go
- Supports microservice extraction if needed

## Migration Summary

### What Was Moved

1. **Database Models**: `src/database.py` → `infrastructure/database/models.py`
2. **Business Logic**: `src/services/` → `domain/services/`
3. **External Services**: `src/llm_client.py` → `infrastructure/external/`
4. **API Routes**: `src/routes/` → `interfaces/api/v1/`
5. **Configuration**: `src/config.py` → `shared/config/settings.py`
6. **Domain Types**: `src/core/types.py` → `domain/entities/types.py`

### What Was Created

1. **Abstract Repositories**: Define data access contracts
2. **Concrete Repositories**: Implement data access using SQLAlchemy
3. **Dependency Injection**: Wire dependencies at application startup
4. **Clean Domain Services**: Business logic without framework dependencies

## Usage Examples

### Using Repository Pattern
```python
# Domain service using repository abstraction
class DocumentService:
    def __init__(self, document_repository: IDocumentRepository):
        self.repository = document_repository
    
    async def process_document(self, text: str) -> ProcessingResult:
        # Business logic here
        document = DocumentEntity(text=text, source="api")
        return await self.repository.create(document)
```

### Dependency Injection
```python
# App dependencies configuration
from app.dependencies import container

# Get service with injected dependencies
document_service = DocumentService(
    document_repository=container.document_repository,
    llm_client=container.llm_client
)
```

## Future Extensions

This architecture supports future enhancements:

1. **Message Queues**: Add to Infrastructure layer
2. **Caching**: Implement repository decorators
3. **Event Sourcing**: Add domain events
4. **CQRS**: Separate read/write models
5. **Microservices**: Extract bounded contexts

## Development Guidelines

1. **Adding New Features**: Start with Domain layer, work outward
2. **Testing**: Write unit tests for Domain, integration tests for Infrastructure
3. **Dependencies**: Always depend on abstractions, not concretions
4. **Cross-Layer Communication**: Use dependency injection, avoid direct imports
5. **External Changes**: Isolate in Infrastructure, update interfaces if needed