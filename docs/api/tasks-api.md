# Tasks API Documentation

## Tổng quan

Task API cung cấp các endpoint để quản lý tasks trong hệ thống Text2Tasks, bao gồm tạo, đọc, cập nhật và liên kết với documents.

## Endpoints

### 1. GET /api/v1/tasks - Danh sách tasks

Lấy danh sách tasks với filtering và sorting.

#### Query Parameters
```
status: Optional[str] - Filter theo status (new|in_progress|blocked|done)
owner: Optional[str] - Filter theo owner
priority: Optional[str] - Filter theo priority (low|medium|high|urgent)
created_by: Optional[str] - Filter theo người tạo
sort_by: Optional[str] - Sort field (created_at|updated_at|title|priority|due_date)
sort_order: Optional[str] - Sort order (asc|desc)
limit: Optional[int] - Giới hạn số lượng (1-200, default: 50)
```

#### Response
```json
[
  {
    "id": "1",
    "title": "Test Task Creation",
    "status": "new",
    "due_date": "2024-12-31",
    "owner": "Claude",
    "source_doc_id": null
  }
]
```

#### Examples
```bash
# Lấy tất cả tasks
curl "http://localhost:8000/api/v1/tasks"

# Filter theo priority high
curl "http://localhost:8000/api/v1/tasks?priority=high"

# Sort theo title ascending
curl "http://localhost:8000/api/v1/tasks?sort_by=title&sort_order=asc"

# Filter và sort kết hợp
curl "http://localhost:8000/api/v1/tasks?status=new&priority=high&sort_by=created_at&sort_order=desc"
```

### 2. POST /api/v1/tasks - Tạo task mới

Tạo một task mới với thông tin chi tiết.

#### Headers
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

#### Request Body
```json
{
  "title": "New Task Title",
  "description": "Optional task description",
  "priority": "medium",
  "due_date": "2024-12-31",
  "owner": "John Doe",
  "document_ids": [1, 2],
  "created_by": "API User"
}
```

#### Response
```json
{
  "id": "5",
  "title": "New Task Title",
  "status": "new",
  "due_date": "2024-12-31",
  "owner": "John Doe",
  "source_doc_id": null
}
```

#### Example
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication system",
    "priority": "high",
    "due_date": "2024-12-25",
    "owner": "Developer",
    "document_ids": [1, 2]
  }'
```

### 3. PATCH /api/v1/tasks/{task_id} - Cập nhật task

Cập nhật thông tin của một task hiện có.

#### Headers
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

#### Request Body
```json
{
  "status": "in_progress",
  "owner": "New Owner",
  "due_date": "2025-01-15"
}
```

#### Response
```json
{
  "message": "Task updated successfully",
  "task": {
    "id": "1",
    "title": "Updated Task",
    "status": "in_progress",
    "updated_fields": ["status", "owner"]
  }
}
```

### 4. GET /api/v1/tasks/{task_id}/documents - Documents của task

Lấy danh sách documents được liên kết với một task.

#### Response
```json
{
  "task_id": "1",
  "documents": [
    {
      "id": 1,
      "text": "Document content preview...",
      "summary": "Document summary",
      "source": "test_source",
      "source_type": "document",
      "created_at": "2025-08-22T09:07:18",
      "linked_at": "2025-08-22T09:07:37"
    }
  ],
  "count": 1
}
```

#### Example
```bash
curl "http://localhost:8000/api/v1/tasks/1/documents"
```

### 5. POST /api/v1/tasks/{task_id}/documents - Link documents

Liên kết documents với một task.

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
  "message": "Successfully linked 3 documents to task 1",
  "task_id": "1",
  "linked_documents": 3
}
```

#### Example
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/1/documents" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3]'
```

### 6. DELETE /api/v1/tasks/{task_id}/documents - Unlink documents

Hủy liên kết documents khỏi một task.

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
  "message": "Successfully unlinked 2 documents from task 1",
  "task_id": "1",
  "unlinked_documents": 2
}
```

## Validation Rules

### Task Creation
- **title**: Required, 1-255 characters
- **description**: Optional, max 2000 characters  
- **priority**: Must be one of: low, medium, high, urgent
- **due_date**: Format YYYY-MM-DD
- **owner**: Max 100 characters
- **document_ids**: Array of valid document IDs

### Task Updates
- **status**: Must be one of: new, in_progress, blocked, done
- **owner**: Max 100 characters
- **due_date**: Format YYYY-MM-DD

## Error Responses

```json
{
  "detail": "Validation error message"
}
```

Common error codes:
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (invalid API key)
- **404**: Not Found (task not exists)
- **500**: Internal Server Error

## Status Transitions

Valid status transitions:
- **new** → in_progress, blocked
- **in_progress** → done, blocked  
- **blocked** → in_progress
- **done** → (no transitions allowed)

## Performance Notes

- Default limit: 50 tasks per request
- Maximum limit: 200 tasks per request
- Sorting và filtering được optimize với database indexes
- Document relationships sử dụng junction table với proper indexing