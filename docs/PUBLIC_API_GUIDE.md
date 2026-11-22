# FocusBoard Public API (v1) Reference Guide

## Authentication
Every request to the FocusBoard Public API must include the `X-API-Key` header:
```http
GET /api/v1/public/v1/tasks HTTP/1.1
Host: localhost:8000
X-API-Key: fb_live_a1b2c3d4e5f6...
```

---

## Task Management

### 1. List Tasks
`GET /api/v1/public/v1/tasks`
- **Required Scope**: `tasks:read`
- **Query Parameters**:
  - `status`: Filter by status (`pending`, `in_progress`, `completed`, `cancelled`)
  - `project_id`: Filter by integer project ID
  - `limit`: Number of items (default 50, max 100)
  - `offset`: Pagination offset (default 0)

### 2. Create Task
`POST /api/v1/public/v1/tasks`
- **Required Scope**: `tasks:write`
- **Headers**:
  - `Idempotency-Key` *(optional)*: Unique string to prevent duplicate creations.
- **Request Body**:
  ```json
  {
    "title": "Upgrade PostgreSQL replica",
    "description": "Failover and upgrade database version",
    "priority": "high",
    "category": "Infrastructure",
    "due_date": "2026-12-01T18:00:00Z",
    "project_id": 4
  }
  ```

### 3. Update Task
`PATCH /api/v1/public/v1/tasks/{task_id}`
- **Required Scope**: `tasks:write`
- **Request Body**: Fields to update (`title`, `status`, `priority`, `due_date`, etc.).

### 4. Delete Task
`DELETE /api/v1/public/v1/tasks/{task_id}`
- **Required Scope**: `tasks:write`
- **Returns**: HTTP 204 No Content.

---

## Projects & Analytics

### List Projects
`GET /api/v1/public/v1/projects`
- **Required Scope**: `projects:read`

### Portfolio Health Analytics
`GET /api/v1/public/v1/analytics/portfolio`
- **Required Scope**: `analytics:read`
- Returns portfolio health score (0-100), active risk distribution, and completion forecasts.
