# Bidirectional Task-Document Relationships

## Tổng quan

Hệ thống Text2Tasks hỗ trợ bidirectional relationships hoàn chỉnh giữa Tasks và Documents, cho phép:

- **Tasks có thể link đến nhiều Documents**
- **Documents có thể link đến nhiều Tasks**  
- **Many-to-many relationships** với metadata tracking
- **Cascade operations** khi delete entities
- **Idempotent operations** để tránh duplicate relationships

## Tính năng đã implemented ✅

### 1. Task-centric Operations
- ✅ `GET /api/v1/tasks/{task_id}/documents` - Lấy documents của task
- ✅ `POST /api/v1/tasks/{task_id}/documents` - Link documents vào task
- ✅ `DELETE /api/v1/tasks/{task_id}/documents` - Unlink documents khỏi task

### 2. Document-centric Operations  
- ✅ `GET /api/v1/documents/{document_id}/tasks` - Lấy tasks của document
- ✅ `POST /api/v1/documents/{document_id}/tasks` - Link tasks vào document
- ✅ `DELETE /api/v1/documents/{document_id}/tasks` - Unlink tasks khỏi document

### 3. Integrated Operations
- ✅ **Task creation với document linking** - Tạo task và link documents trong một operation
- ✅ **Bulk operations** - Link/unlink nhiều items cùng lúc
- ✅ **Metadata tracking** - Track created_at, created_by cho mỗi relationship

### 4. Database Features
- ✅ **Junction table** với proper constraints và indexes
- ✅ **Unique constraints** prevent duplicate relationships
- ✅ **Cascade deletes** maintain referential integrity
- ✅ **Performance optimization** với indexed queries

## Use Cases Thực tế

### 1. Project Management
```bash
# Tạo epic task và link requirements documents
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "User Authentication System",
    "description": "Implement complete auth system",
    "priority": "high",
    "owner": "Backend Team",
    "document_ids": [1, 2, 3]  // Requirements, specs, design docs
  }'
```

### 2. Knowledge Management
```bash
# Link research document đến multiple implementation tasks
curl -X POST "http://localhost:8000/api/v1/documents/1/tasks" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3, 4]'  // Multiple related tasks
```

### 3. Traceability
```bash  
# Find all documents related to a task
curl "http://localhost:8000/api/v1/tasks/1/documents"

# Find all tasks implementing a requirement document  
curl "http://localhost:8000/api/v1/documents/1/tasks"
```

## Technical Implementation

### Database Schema
```sql
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

### Repository Layer
```python
# Task Repository có methods:
def link_documents(self, task_id: int, document_ids: List[int], created_by: Optional[str] = None) -> bool
def unlink_documents(self, task_id: int, document_ids: List[int]) -> bool  
def get_linked_documents(self, task_id: int) -> List[Dict[str, Any]]

# Plus inverse operations:
def get_tasks_for_document(self, document_id: int) -> List[Dict[str, Any]]
def link_tasks_to_document(self, document_id: int, task_ids: List[int], created_by: Optional[str] = None) -> bool
def unlink_tasks_from_document(self, document_id: int, task_ids: List[int]) -> bool
```

## API Response Examples

### Task với Documents
```json
{
  "task_id": "1",
  "documents": [
    {
      "id": 1,
      "text": "Requirements document preview...",
      "summary": "Auth requirements", 
      "source": "confluence",
      "source_type": "document",
      "created_at": "2025-08-22T09:07:18",
      "linked_at": "2025-08-22T09:15:30"
    }
  ],
  "count": 1
}
```

### Document với Tasks  
```json
{
  "document_id": "1",
  "tasks": [
    {
      "id": "1",
      "title": "Implement JWT auth",
      "description": "Add JWT authentication system",
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

## Performance Characteristics

### Optimized Queries
- **Indexed lookups** trên task_id và document_id
- **JOIN operations** được optimize với proper indexes
- **Batch operations** reduce API calls

### Scalability
- **Junction table** scales to millions of relationships
- **Pagination support** cho large result sets  
- **Query optimization** với database indexes

## Error Handling

### Validation
- ✅ **Entity existence** - Task/Document must exist before linking
- ✅ **Duplicate prevention** - Unique constraints prevent duplicates
- ✅ **Batch validation** - Invalid IDs ignored, valid ones processed

### Idempotency
- ✅ **Safe operations** - Link existing relationship = no error
- ✅ **Unlink non-existing** = no error
- ✅ **Consistent state** maintained across operations

## Testing Verification ✅

### Basic Operations
```bash
# ✅ Create task with documents
curl -X POST ".../tasks" -d '{"title":"Test", "document_ids":[1,2]}'

# ✅ Get task documents  
curl ".../tasks/1/documents" # Returns 2 documents

# ✅ Get document tasks
curl ".../documents/1/tasks" # Returns 1 task

# ✅ Bidirectional consistency verified
```

### Advanced Operations
```bash  
# ✅ Bulk linking
curl -X POST ".../tasks/1/documents" -d '[3,4,5]'

# ✅ Unlink operations
curl -X DELETE ".../tasks/1/documents" -d '[2]'

# ✅ Cross-verification
curl ".../documents/2/tasks" # Task 1 no longer appears
```

## Future Enhancements

### Possible Improvements
- [ ] **Relationship types** (requires, implements, references)
- [ ] **Versioning** track relationship changes
- [ ] **Bulk operations UI** for easy management
- [ ] **Relationship analytics** (most linked documents/tasks)
- [ ] **Graph visualization** of relationships

### Performance Optimizations
- [ ] **Caching layer** for frequently accessed relationships  
- [ ] **Denormalized views** for complex queries
- [ ] **Background sync** for large bulk operations

## Conclusion

Bidirectional relationships đã được implement hoàn chỉnh với:

✅ **Full CRUD operations** cho cả hai directions
✅ **Performance optimization** với proper indexing  
✅ **Data integrity** với constraints và cascades
✅ **API consistency** với error handling
✅ **Metadata tracking** cho audit trail
✅ **Testing verification** cho tất cả use cases

Hệ thống sẵn sàng để support complex project management workflows và knowledge management scenarios.