# Task-Document Relationships API

## Tổng quan

Hệ thống Text2Tasks hỗ trợ bidirectional relationships giữa Tasks và Documents thông qua một junction table được tối ưu hóa. Mọi relationship đều có metadata như created_at và created_by.

## Kiến trúc Relationships

### Database Schema
```sql
-- Junction table cho many-to-many relationship
CREATE TABLE task_documents (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(task_id, document_id)
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_task_documents_task_id ON task_documents(task_id);
CREATE INDEX idx_task_documents_document_id ON task_documents(document_id);
CREATE INDEX idx_task_documents_created_at ON task_documents(created_at);
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks/{task_id}/documents` | Lấy documents của task |
| POST | `/api/v1/tasks/{task_id}/documents` | Link documents vào task |  
| DELETE | `/api/v1/tasks/{task_id}/documents` | Unlink documents khỏi task |
| GET | `/api/v1/documents/{document_id}/tasks` | Lấy tasks của document |
| POST | `/api/v1/documents/{document_id}/tasks` | Link tasks vào document |
| DELETE | `/api/v1/documents/{document_id}/tasks` | Unlink tasks khỏi document |

## Bidirectional Operations

### 1. Task → Documents (Task-centric view)

#### Link Documents to Task
```bash
# Link documents 1,2,3 to task 5
curl -X POST "http://localhost:8000/api/v1/tasks/5/documents" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3]'
```

#### Get Documents for Task
```bash
# Get all documents linked to task 5
curl "http://localhost:8000/api/v1/tasks/5/documents"
```

Response:
```json
{
  "task_id": "5",
  "documents": [
    {
      "id": 1,
      "text": "Document content preview...",
      "summary": "Requirements document",
      "source": "confluence",
      "source_type": "document",
      "created_at": "2025-08-22T09:07:18",
      "linked_at": "2025-08-22T09:15:30"
    }
  ],
  "count": 1
}
```

### 2. Document → Tasks (Document-centric view)

#### Link Tasks to Document  
```bash
# Link tasks 1,2,3 to document 5
curl -X POST "http://localhost:8000/api/v1/documents/5/tasks" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3]'
```

#### Get Tasks for Document
```bash  
# Get all tasks linked to document 5
curl "http://localhost:8000/api/v1/documents/5/tasks"
```

Response:
```json
{
  "document_id": "5", 
  "tasks": [
    {
      "id": "1",
      "title": "Implement authentication",
      "description": "Add JWT-based auth system",
      "status": "new",
      "priority": "high", 
      "due_date": "2024-12-31",
      "owner": "John Doe",
      "created_by": "PM",
      "created_at": "2025-08-22T09:01:02",
      "linked_at": "2025-08-22T09:15:30"
    }
  ],
  "count": 1
}
```

## Advanced Usage Patterns

### 1. Task Creation với Document Linking

Tạo task mới và link documents trong một operation:

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement user dashboard", 
    "description": "Create responsive dashboard UI",
    "priority": "high",
    "due_date": "2025-01-15",
    "owner": "Frontend Team",
    "document_ids": [1, 2, 3],
    "created_by": "Product Manager"
  }'
```

### 2. Bulk Operations

#### Link Multiple Documents to Multiple Tasks
```bash
# Script để link document 1 vào nhiều tasks
for task_id in 1 2 3 4 5; do
  curl -X POST "http://localhost:8000/api/v1/tasks/$task_id/documents" \
    -H "X-API-Key: your_api_key_here" \
    -H "Content-Type: application/json" \
    -d '[1]'
done
```

#### Unlink Operations
```bash
# Remove document 2 khỏi task 1
curl -X DELETE "http://localhost:8000/api/v1/tasks/1/documents" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '[2]'
```

### 3. Relationship Querying

#### Find All Related Items
```bash
# Find all documents related to task 1  
DOCS=$(curl -s "http://localhost:8000/api/v1/tasks/1/documents" | jq -r '.documents[].id')

# For each document, find other related tasks
for doc_id in $DOCS; do
  echo "Document $doc_id is related to tasks:"
  curl -s "http://localhost:8000/api/v1/documents/$doc_id/tasks" | jq -r '.tasks[].id'
done
```

## Relationship Metadata

Mỗi relationship có metadata được track:

```json
{
  "linked_at": "2025-08-22T09:15:30",  // Timestamp khi link được tạo
  "created_by": "john.doe"             // User tạo relationship (optional)
}
```

### Set created_by khi linking
```bash
# Link với metadata
curl -X POST "http://localhost:8000/api/v1/tasks/1/documents" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1, 2],
    "created_by": "john.doe"
  }'
```

## Error Handling

### Common Errors

```json
// Task không tồn tại
{
  "detail": "Task not found or no valid documents provided"
}

// Document không tồn tại  
{
  "detail": "Document not found or no valid tasks provided"
}

// Invalid IDs
{
  "detail": "Invalid task ID format"
}
```

### Idempotent Operations

Tất cả linking operations đều idempotent:

```bash
# Link document 1 to task 1 nhiều lần = same result  
curl -X POST "http://localhost:8000/api/v1/tasks/1/documents" \
  -H "X-API-Key: your_api_key_here" \
  -d '[1]'
  
curl -X POST "http://localhost:8000/api/v1/tasks/1/documents" \
  -H "X-API-Key: your_api_key_here" \
  -d '[1]'  # No error, no duplicate created
```

## Performance Characteristics

### Optimizations
- **Unique constraints** prevent duplicate relationships
- **Cascade deletes** maintain referential integrity  
- **Indexed queries** for fast lookups
- **Batch operations** support multiple IDs in single request

### Limits
- Maximum 100 IDs per batch operation
- Junction table automatically indexed
- Soft limit 1000 relationships per task/document (performance)

## Integration Examples

### Full Workflow Example

```bash
#!/bin/bash
API_KEY="your_api_key_here"

# 1. Create một document
DOC_RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "X-API-Key: $API_KEY" \
  -F "text=User authentication requirements and specifications" \
  -F "summary=Auth requirements doc")
  
DOC_ID=$(echo $DOC_RESPONSE | jq -r '.document.id')

# 2. Create task và link document
TASK_RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Implement JWT authentication\",
    \"description\": \"Based on requirements document\",
    \"priority\": \"high\",
    \"document_ids\": [$DOC_ID],
    \"created_by\": \"automation_script\"
  }")
  
TASK_ID=$(echo $TASK_RESPONSE | jq -r '.id')

# 3. Verify relationship
echo "Task $TASK_ID is linked to these documents:"
curl -s "http://localhost:8000/api/v1/tasks/$TASK_ID/documents" | jq '.documents[] | {id, summary}'

echo "Document $DOC_ID is linked to these tasks:"  
curl -s "http://localhost:8000/api/v1/documents/$DOC_ID/tasks" | jq '.tasks[] | {id, title}'
```

## Database Queries Behind the Scenes

### Get Documents for Task
```sql
SELECT d.id, d.text, d.summary, d.source, d.source_type, d.created_at, td.created_at as linked_at
FROM documents d
JOIN task_documents td ON d.id = td.document_id  
WHERE td.task_id = ?
ORDER BY td.created_at DESC
```

### Get Tasks for Document  
```sql
SELECT t.id, t.title, t.description, t.status, t.priority, t.due_date, t.owner, t.created_by, t.created_at, td.created_at as linked_at
FROM tasks t
JOIN task_documents td ON t.id = td.task_id
WHERE td.document_id = ?  
ORDER BY td.created_at DESC
```