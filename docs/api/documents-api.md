# Documents API Documentation

## Tổng quan

Documents API cung cấp các endpoint để quản lý documents trong hệ thống Text2Tasks, bao gồm tạo, đọc, và liên kết với tasks.

## Endpoints

### 1. GET /api/v1/documents - Danh sách documents

Lấy danh sách tất cả documents với pagination.

#### Query Parameters
```
limit: Optional[int] - Số lượng documents mỗi page (1-200, default: 50)
offset: Optional[int] - Offset cho pagination (default: 0)
```

#### Response
```json
{
  "documents": [
    {
      "id": 1,
      "text": "Document content preview (max 200 chars)...",
      "summary": "Document summary",
      "source": "test_source",
      "source_type": "document",
      "created_at": "2025-08-22T09:07:18"
    }
  ],
  "count": 2,
  "limit": 50,
  "offset": 0
}
```

#### Examples
```bash
# Lấy documents đầu tiên
curl "http://localhost:8000/api/v1/documents"

# Pagination - page 2 với 10 items mỗi page
curl "http://localhost:8000/api/v1/documents?limit=10&offset=10"

# Lấy 100 documents gần nhất
curl "http://localhost:8000/api/v1/documents?limit=100"
```

### 2. POST /api/v1/documents - Tạo document mới

Tạo một document mới trong hệ thống.

#### Headers
```
X-API-Key: your_api_key_here
Content-Type: application/x-www-form-urlencoded
```

#### Form Parameters
```
text: str - Nội dung document (required, max 50000 characters)
summary: Optional[str] - Tóm tắt document
source: Optional[str] - Nguồn document (default: "manual")
source_type: Optional[str] - Loại nguồn (default: "document")
```

#### Response
```json
{
  "message": "Document created successfully",
  "document": {
    "id": "3",
    "text": "Document content preview...",
    "summary": "Document summary",
    "source": "manual",
    "source_type": "document",
    "created_at": "2025-08-22T09:30:00"
  }
}
```

#### Example
```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "X-API-Key: your_api_key_here" \
  -F "text=This is a new document about project requirements and specifications." \
  -F "summary=Project requirements document" \
  -F "source=manual_input" \
  -F "source_type=document"
```

### 3. GET /api/v1/documents/{document_id}/tasks - Tasks của document

Lấy danh sách tasks được liên kết với một document.

#### Response
```json
{
  "document_id": "1",
  "tasks": [
    {
      "id": "1",
      "title": "Test Task Creation",
      "description": "This is a test task created via API",
      "status": "new",
      "priority": "high",
      "due_date": "2024-12-31",
      "owner": "Claude",
      "created_by": "API Test",
      "created_at": "2025-08-22T09:01:02.318816",
      "linked_at": "2025-08-22T09:07:37"
    }
  ],
  "count": 1
}
```

#### Example
```bash
curl "http://localhost:8000/api/v1/documents/1/tasks"
```

### 4. POST /api/v1/documents/{document_id}/tasks - Link tasks

Liên kết tasks với một document.

#### Headers
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

#### Request Body
```json
[1, 2, 3]
```

#### Response
```json
{
  "message": "Successfully linked 3 tasks to document 1",
  "document_id": "1",
  "linked_tasks": 3
}
```

#### Example
```bash
curl -X POST "http://localhost:8000/api/v1/documents/1/tasks" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3]'
```

### 5. DELETE /api/v1/documents/{document_id}/tasks - Unlink tasks

Hủy liên kết tasks khỏi một document.

#### Headers
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

#### Request Body
```json
[1, 2]
```

#### Response
```json
{
  "message": "Successfully unlinked 2 tasks from document 1",
  "document_id": "1",
  "unlinked_tasks": 2
}
```

#### Example
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/1/tasks" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '[1, 2]'
```

## Data Models

### Document Object
```json
{
  "id": "integer - Unique document ID",
  "text": "string - Document content (truncated in list view)",
  "summary": "string - Document summary", 
  "source": "string - Source identifier",
  "source_type": "string - Type of source (document, email, meeting, etc.)",
  "created_at": "string - ISO timestamp"
}
```

### Task Object (in document relationships)
```json
{
  "id": "string - Task ID",
  "title": "string - Task title",
  "description": "string - Task description",
  "status": "string - Task status",
  "priority": "string - Task priority", 
  "due_date": "string - Due date (YYYY-MM-DD)",
  "owner": "string - Task owner",
  "created_by": "string - Who created the task",
  "created_at": "string - When task was created",
  "linked_at": "string - When link was created"
}
```

## Validation Rules

### Document Creation
- **text**: Required, minimum 1 character, maximum 50,000 characters
- **summary**: Optional, no length limit
- **source**: Optional, defaults to "manual" 
- **source_type**: Optional, defaults to "document"

### Task Linking
- **task_ids**: Array of valid task IDs
- Document must exist
- Tasks must exist
- Duplicate links are ignored (idempotent operation)

## Error Responses

```json
{
  "detail": "Error message"
}
```

Common error codes:
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (invalid API key) 
- **404**: Not Found (document not exists)
- **500**: Internal Server Error

Common validation errors:
- "Document text is required"
- "Document text too long (max 50000 characters)"
- "Document not found or no valid tasks provided"

## Performance Notes

### Pagination
- Default limit: 50 documents per request
- Maximum limit: 200 documents per request
- Use offset for pagination: `?limit=50&offset=100`

### Text Handling
- List endpoint truncates text to 200 characters with "..."
- Full text available via detail endpoints or task relationships
- Text content is validated for security

### Database Optimization
- Documents ordered by created_at DESC by default
- Proper indexing on frequently queried fields
- Junction table optimized for relationship queries

## Integration Examples

### Create Document + Link to Existing Tasks
```bash
# 1. Create document
DOC_ID=$(curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "X-API-Key: your_api_key_here" \
  -F "text=Requirements for user authentication system" \
  -F "summary=Auth requirements" | jq -r '.document.id')

# 2. Link to existing tasks  
curl -X POST "http://localhost:8000/api/v1/documents/$DOC_ID/tasks" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3]'
```

### Find All Tasks for a Document
```bash
# Get document's tasks with full details
curl "http://localhost:8000/api/v1/documents/1/tasks" | jq '.tasks[] | {id, title, status, priority}'
```