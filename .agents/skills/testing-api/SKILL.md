---
name: testing-gestor-tareas-api
description: Test the gestor-tareas-api REST endpoints end-to-end. Use when verifying API changes.
---

# Testing gestor-tareas-api

## Prerequisites
- Python 3.12+ with dependencies from `requirements.txt`
- No external services or secrets required — uses local SQLite (`tareas.db`)

## Running Unit Tests
```bash
python -m pytest tests/ -v
```
Tests use an in-memory SQLite database (StaticPool) so they don't affect `tareas.db`.

## Running the Server Locally
```bash
# Start with a clean database
rm -f tareas.db
uvicorn aplicacion.principal:app --host 0.0.0.0 --port 8000
```

## Manual E2E Testing via curl
This is a pure REST API (no UI). Test via curl against `http://localhost:8000`.

### Key Endpoints
- `GET /tasks/` — list all tasks
- `GET /tasks/{task_id}` — get task by ID
- `GET /tasks/status/{status}` — filter tasks by status (`pending`, `in_progress`, `done`)
- `POST /tasks/` — create task (body: `{"title": "...", "status": "pending"}`)
- `PATCH /tasks/{task_id}` — update task (cannot update tasks with status `done`)
- `DELETE /tasks/{task_id}` — delete task

### Example: Seed and Test
```bash
# Create tasks
curl -s -X POST http://localhost:8000/tasks/ -H 'Content-Type: application/json' -d '{"title":"Test task","status":"pending"}'

# Filter by status
curl -s http://localhost:8000/tasks/status/pending | python3 -m json.tool

# Invalid status returns 422
curl -s -w '\nHTTP_CODE: %{http_code}\n' http://localhost:8000/tasks/status/invalid
```

## Notes
- No recording needed — all testing is shell-based (curl + pytest)
- The `TaskStatus` enum accepts: `pending`, `in_progress`, `done`
- Tasks with status `done` cannot be updated (returns 400)
- Invalid enum values on path params return 422 automatically via FastAPI validation

## Devin Secrets Needed
None — the app uses local SQLite with no authentication.
