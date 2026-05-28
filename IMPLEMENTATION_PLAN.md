# Implementation Plan: API/Worker Separation

## Decisions

| Decision | Choice |
|---|---|
| Task queue | Celery with Redis broker |
| Chat agent loop | Moved to worker, streamed via WebSocket |
| Job status delivery | WebSocket (Redis Pub/Sub bridge) |
| Job persistence | PostgreSQL `jobs` table |
| Dev experience | Separate worker process (always) |

---

## Current State

There is no background-job infrastructure. All work -- LLM calls, PDF parsing, embedding
generation, and the full chat agent loop (up to 6 LLM iterations) -- runs inline inside HTTP
request handlers. The longest operations are:

1. **Chat agent loop** (`POST /chat/sessions/{id}/messages`) -- up to 6 sequential LLM calls
2. **Transcript upload** (`POST /students/me/transcript`) -- PDF parse + LLM extraction + embedding
3. **ArXiv ingestion** (`POST /chairs/{id}/documents/arxiv`) -- HTTP fetch + embedding
4. **Thesis creation** (`POST /theses`) -- embedding generation

---

## Phase 1 -- Infrastructure (Celery + Redis)

### 1.1 Add Redis to Docker Compose

Edit `docker-compose.yml`:

```yaml
services:
  db:
    # ... unchanged ...

  redis:
    image: redis:7-alpine
    container_name: study-os-thesis-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy noeviction
      --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  db-data:
  redis-data:
```

- `noeviction` prevents Redis from silently dropping Celery keys under memory pressure.
- `appendonly yes` persists data across restarts.

### 1.2 Add Python Dependencies

Add to `backend/pyproject.toml` `[project] dependencies`:

```
"celery[redis]>=5.6",
"redis>=5.0",
```

Add to `[dependency-groups] dev`:

```
"pytest-cov>=6.0",
"respx>=0.22",
```

### 1.3 Add `REDIS_URL` to Config

Edit `backend/app/config.py` -- add field to `Settings`:

```python
redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
```

Add to `backend/.env.example`:

```
REDIS_URL=redis://localhost:6379/0
```

### 1.4 Create the Celery Worker Module

New files:

```
backend/app/worker/
  __init__.py
  celery_app.py       # Celery() instance + autodiscover
  celery_config.py    # Broker/backend/serialization settings
  utils.py            # run_async() helper
  publisher.py        # Redis Pub/Sub event publisher
```

**`celery_app.py`**

```python
from celery import Celery

celery_app = Celery("study_os_thesis")
celery_app.config_from_object("app.worker.celery_config")
celery_app.autodiscover_tasks([
    "app.theses",
    "app.chairs",
    "app.students",
    "app.chat",
])
```

**`celery_config.py`**

```python
import os

broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/0")

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

task_track_started = True
task_acks_late = True
worker_prefetch_multiplier = 1
task_reject_on_worker_lost = True

result_expires = 86400              # 24 hours
result_extended = True

broker_transport_options = {
    "visibility_timeout": 3600,
}

worker_concurrency = 4
```

**`utils.py`**

```python
import asyncio
from typing import TypeVar, Coroutine, Any

T = TypeVar("T")

def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine from a sync Celery task.

    Each call creates a fresh event loop. This is safe because Celery
    prefork workers are separate processes with no pre-existing loop.
    """
    return asyncio.run(coro)
```

**`publisher.py`**

```python
import json
import logging
from datetime import datetime, timezone

import redis as sync_redis

logger = logging.getLogger(__name__)

def publish_event(
    redis_url: str,
    *,
    event_type: str,
    job_id: str,
    user_id: int,
    status: str,
    data: dict | None = None,
) -> None:
    """Publish an event to Redis Pub/Sub from a Celery worker."""
    payload = {
        "type": event_type,
        "job_id": job_id,
        "user_id": user_id,
        "status": status,
        "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        r = sync_redis.from_url(redis_url)
        r.publish("job_events", json.dumps(payload))
    except Exception:
        logger.exception("Failed to publish event to Redis")
```

Handle forked-process engine disposal via Celery signal:

```python
# in celery_app.py or a signals.py
from celery.signals import worker_process_init

@worker_process_init.connect
def on_worker_init(**kwargs):
    import asyncio
    from app.db import engine
    asyncio.run(engine.dispose())
```

### 1.5 Update `debug.sh`

Add Celery worker as a third background process alongside uvicorn and vite:

```bash
CELERY_PID=""

# In run_app():
info "Starting Celery worker..."
(cd "$BACKEND_DIR" && exec uv run celery \
    -A app.worker.celery_app worker \
    --loglevel=info \
    --concurrency=2) &
CELERY_PID=$!

# In cleanup():
kill_pid "$CELERY_PID"
```

Update usage output to mention the worker.

---

## Phase 2 -- Jobs Table & Domain

### 2.1 Database Model

New file `backend/app/models/job.py`:

```python
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class JobType(str, enum.Enum):
    embed_thesis = "embed_thesis"
    embed_chair = "embed_chair"
    ingest_arxiv = "ingest_arxiv"
    parse_transcript = "parse_transcript"
    chat_turn = "chat_turn"
    generate_proposal = "generate_proposal"


class JobStatus(str, enum.Enum):
    pending = "pending"
    started = "started"
    success = "success"
    failure = "failure"
    retry = "retry"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type"), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), nullable=False, default=JobStatus.pending
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    input_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

### 2.2 Alembic Migration

```bash
cd backend && uv run alembic revision --autogenerate -m "add_jobs_table"
```

This creates migration `0009_add_jobs_table.py`.

### 2.3 Jobs Domain Module

Create `backend/app/jobs/` with the standard structure:

```
backend/app/jobs/
  __init__.py
  controller.py    # GET /api/jobs/{id}, GET /api/jobs
  service.py       # create_job, mark_started, mark_success, mark_failure, mark_retry
  repository.py    # CRUD against the jobs table
  schemas.py       # JobCreate, JobOut, JobType, JobStatus (Pydantic)
  deps.py          # JobServiceDep
```

**Endpoints:**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/jobs/{id}` | `CurrentUserDep` | Get job status (user can only see own jobs) |
| `GET` | `/api/jobs` | `CurrentUserDep` | List user's jobs, optional `?type=...&status=...` |

**Service methods:**

```python
class JobService:
    async def create_job(type, user_id, input_data, celery_task_id) -> Job
    async def mark_started(job_id) -> Job
    async def mark_success(job_id, result_data) -> Job
    async def mark_failure(job_id, error) -> Job
    async def mark_retry(job_id) -> Job
    async def get_job(job_id, user_id) -> Job      # enforces ownership
    async def list_jobs(user_id, type?, status?) -> list[Job]
```

### 2.4 Register Router

Edit `backend/app/main.py` to include the jobs router:

```python
from app.jobs import controller as jobs_router
app.include_router(jobs_router.router, prefix="/api/jobs", tags=["jobs"])
```

---

## Phase 3 -- WebSocket Layer

### 3.1 Connection Manager

New file `backend/app/ws/manager.py`:

```python
class ConnectionManager:
    """Tracks active WebSocket connections by user_id."""

    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, ws: WebSocket) -> None
    def disconnect(self, user_id: int, ws: WebSocket) -> None
    async def send_to_user(self, user_id: int, data: dict) -> None
```

- `send_to_user` iterates over all connections for a user and sends JSON.
- Stale connections (where `send_json` raises) are silently skipped.

### 3.2 Redis Pub/Sub Listener

New file `backend/app/ws/listener.py`:

```python
async def redis_listener(manager: ConnectionManager, redis_url: str) -> None:
    """Subscribe to 'job_events' channel and dispatch to WebSockets."""
```

- Uses `redis.asyncio.Redis` with `pubsub.subscribe("job_events")`.
- Deserializes each message, extracts `user_id`, calls `manager.send_to_user`.
- Handles malformed JSON and missing fields gracefully (log + skip).

### 3.3 WebSocket Endpoint

New file `backend/app/ws/controller.py`:

```python
@router.websocket("/api/ws")
async def ws_job_updates(websocket: WebSocket):
    # 1. Accept connection
    # 2. Authenticate via token (query param or first message)
    # 3. Register in ConnectionManager
    # 4. Keep alive (receive loop)
    # 5. On disconnect, remove from ConnectionManager
```

### 3.4 Start Listener in Lifespan

Edit `backend/app/main.py` lifespan:

```python
@asynccontextmanager
async def _lifespan(app: FastAPI):
    # ... existing startup ...
    app.state.ws_manager = ConnectionManager()
    listener_task = asyncio.create_task(
        redis_listener(app.state.ws_manager, settings.redis_url)
    )
    yield
    listener_task.cancel()
    # ... existing shutdown ...
```

---

## Phase 4 -- Migrate Ingestion Tasks to Worker

For each domain, the pattern is:

1. Extract the heavy work into a **Celery task** (`tasks.py`) that wraps the existing async service.
2. Modify the **controller** to create a job, dispatch the task, and return immediately.
3. The **task** updates job status and publishes WebSocket events on completion/failure.

### 4.1 Thesis Embedding

**Current flow** (`POST /api/theses`):
```
validate -> embed(title+abstract) -> persist thesis -> return thesis
```

**New flow:**
```
validate -> persist thesis (embedding=None) -> create job -> dispatch embed_thesis task -> return {thesis, job_id}

Worker:
  embed_thesis(thesis_id) -> generate embedding -> update thesis.embedding -> mark job success -> publish event
```

New file: `backend/app/theses/tasks.py`

### 4.2 ArXiv Paper Ingestion

**Current flow** (`POST /api/chairs/{id}/documents/arxiv`):
```
validate -> fetch ArXiv API -> embed abstract -> persist document -> return document
```

**New flow:**
```
validate chair exists + arxiv_id format -> create job -> dispatch ingest_arxiv task -> return {job_id}

Worker:
  ingest_arxiv(chair_id, arxiv_id) -> fetch metadata -> embed -> persist -> mark job success -> publish event
```

New file: `backend/app/chairs/tasks.py`

### 4.3 Transcript Upload

**Current flow** (`POST /api/students/me/transcript`):
```
validate file -> extract PDF text -> LLM parse -> compute GPA -> embed courses -> upsert profile -> return profile
```

**New flow:**
```
validate file type/size -> store PDF bytes temporarily -> create job -> dispatch parse_transcript task -> return {job_id}

Worker:
  parse_transcript(user_id, pdf_bytes_ref) -> extract text -> LLM parse -> GPA -> embed -> upsert -> mark job success -> publish event
```

New file: `backend/app/students/tasks.py`

### 4.4 Chair Creation Embedding

**Current flow** (`POST /api/chairs`):
```
create chair -> embed description -> store ChairDocument -> return chair
```

**New flow:**
```
create chair row -> create job -> dispatch embed_chair_description task -> return {chair, job_id}

Worker:
  embed_chair_description(chair_id) -> embed description -> store ChairDocument -> mark job success -> publish event
```

Added to: `backend/app/chairs/tasks.py`

---

## Phase 5 -- Migrate Chat Agent Loop to Worker

This is the most complex migration because the chat agent loop is iterative and the client
needs real-time feedback.

### 5.1 New Chat Flow

**Current flow** (`POST /api/chat/sessions/{id}/messages`):
```
persist user message -> run agent loop (up to 6 LLM iterations) -> persist all messages -> return messages
```

**New flow:**
```
persist user message -> create job -> dispatch process_chat_turn task -> return {job_id, message_id}

Worker:
  process_chat_turn(session_id, user_id, content):
    publish chat_turn_started event
    for each LLM iteration:
      call LLM
      persist message(s)
      publish chat_message event (so client sees it in real-time)
      if tool_call:
        publish chat_tool_call event
        execute tool
        persist tool result message
    publish chat_turn_completed event
    mark job success
```

### 5.2 WebSocket Event Types for Chat

| Event type | When | Data |
|---|---|---|
| `chat_turn_started` | Agent loop begins | `{session_id}` |
| `chat_tool_call` | Agent invokes a tool | `{session_id, tool_name, arguments}` |
| `chat_message` | Each assistant/tool message | `{session_id, message}` (full `MessageOut`) |
| `chat_turn_completed` | Agent loop finished | `{session_id, message_count}` |

### 5.3 Frontend Changes

- `frontend/src/api/ws.ts` -- new WebSocket client module
- `frontend/src/pages/Chat.tsx` -- listen on WebSocket for `chat_*` events instead of
  waiting for the HTTP response
- Display incoming messages in real-time
- Show tool-call indicators ("Searching theses...", "Generating proposal...")
- Handle errors (job failure -> error message in chat)

### 5.4 Controller Changes

Edit `backend/app/chat/controller.py`:

- `POST /sessions/{id}/messages` returns `202` with `{job_id, message_id}` instead of the
  full message list.
- `GET /sessions/{id}/messages` remains unchanged (returns all persisted messages).

New file: `backend/app/chat/tasks.py`

---

## Phase 6 -- Error Handling & Retries

### 6.1 Retry Configuration

Per-task retry policy:

| Task | max_retries | retry_delay | Retryable errors |
|---|---|---|---|
| `embed_thesis` | 3 | 60s | `ConnectionError`, `TimeoutError`, LLM overloaded |
| `embed_chair_description` | 3 | 60s | same |
| `ingest_arxiv` | 3 | 60s | same + `httpx.TimeoutException` |
| `parse_transcript` | 3 | 120s | same + LLM timeout |
| `process_chat_turn` | 2 | 30s | LLM connection errors only |

Non-retryable errors (fail immediately):
- `NotFoundException` -- resource doesn't exist
- `ValidationError` -- bad input data
- `AlreadyExistsException` -- duplicate resource

### 6.2 Task Timeouts

| Task | soft_time_limit | time_limit |
|---|---|---|
| `embed_thesis` | 120s | 180s |
| `embed_chair_description` | 120s | 180s |
| `ingest_arxiv` | 120s | 180s |
| `parse_transcript` | 300s | 360s |
| `process_chat_turn` | 600s | 660s |

### 6.3 Dead Letter Handling

Tasks that exhaust all retries:
1. Update `job.status = failure`, store traceback in `job.error`
2. Publish a failure event to the WebSocket
3. Log at `ERROR` level with full context (task name, args, traceback)

---

## Phase 7 -- Development & Observability

### 7.1 `debug.sh` Updates

Already covered in Phase 1.5. The worker is launched as a third background process with its
own PID, added to the cleanup trap.

### 7.2 Logging

Configure Celery worker logging to use the same `log_config.json` format:

```bash
celery -A app.worker.celery_app worker \
    --loglevel=info \
    --logfile=logs/celery.log
```

Ensure task_id and job_id are included in structured log context.

### 7.3 Optional: Flower Dashboard

Add `flower` to dev dependencies:

```bash
celery -A app.worker.celery_app flower --port=5555
```

Provides web UI for monitoring tasks, workers, and queues at `http://localhost:5555`.

---

## File Change Summary

### New Files (~17)

| File | Phase | Description |
|---|---|---|
| `backend/app/worker/__init__.py` | 1 | Package init |
| `backend/app/worker/celery_app.py` | 1 | Celery instance + autodiscover + signal handler |
| `backend/app/worker/celery_config.py` | 1 | Broker, backend, serialization, concurrency |
| `backend/app/worker/utils.py` | 1 | `run_async()` helper |
| `backend/app/worker/publisher.py` | 1 | Redis Pub/Sub event publisher |
| `backend/app/models/job.py` | 2 | Job SQLAlchemy model |
| `backend/alembic/versions/0009_*.py` | 2 | Migration for jobs table |
| `backend/app/jobs/__init__.py` | 2 | Package init |
| `backend/app/jobs/controller.py` | 2 | Job status endpoints |
| `backend/app/jobs/service.py` | 2 | Job lifecycle management |
| `backend/app/jobs/repository.py` | 2 | Job data access |
| `backend/app/jobs/schemas.py` | 2 | Pydantic schemas |
| `backend/app/jobs/deps.py` | 2 | DI wiring |
| `backend/app/ws/manager.py` | 3 | WebSocket connection manager |
| `backend/app/ws/listener.py` | 3 | Redis Pub/Sub -> WebSocket bridge |
| `backend/app/ws/controller.py` | 3 | WebSocket endpoint |
| `backend/app/theses/tasks.py` | 4 | Thesis embedding task |
| `backend/app/chairs/tasks.py` | 4 | ArXiv ingestion + chair embedding tasks |
| `backend/app/students/tasks.py` | 4 | Transcript parsing task |
| `backend/app/chat/tasks.py` | 5 | Chat agent loop task |
| `frontend/src/api/ws.ts` | 5 | WebSocket client |

### Edited Files (~12)

| File | Phase | Changes |
|---|---|---|
| `docker-compose.yml` | 1 | Add Redis service + volume |
| `backend/pyproject.toml` | 1 | Add celery, redis, test deps |
| `backend/app/config.py` | 1 | Add `REDIS_URL` field |
| `backend/.env.example` | 1 | Add `REDIS_URL` |
| `backend/app/models/__init__.py` | 2 | Export Job, JobType, JobStatus |
| `backend/app/main.py` | 2,3 | Register jobs router, WS router, start Redis listener |
| `debug.sh` | 1 | Launch Celery worker process |
| `backend/app/theses/controller.py` | 4 | Dispatch to worker, return job_id |
| `backend/app/chairs/controller.py` | 4 | Dispatch to worker, return job_id |
| `backend/app/students/controller.py` | 4 | Dispatch to worker, return job_id |
| `backend/app/chat/controller.py` | 5 | Dispatch to worker, return 202 |
| `backend/app/chat/service.py` | 5 | Add event publishing hooks |
| `frontend/src/pages/Chat.tsx` | 5 | WebSocket-based message streaming |

---

## Implementation Order

```
Phase 1 (Infrastructure)     ← Redis + Celery skeleton
  |
Phase 2 (Jobs table)         ← Persistent job tracking
  |
Phase 3 (WebSocket)          ← Real-time event delivery
  |
Phase 4 (Ingestion tasks)    ← Move embedding/ingestion (low risk, idempotent)
  |
Phase 5 (Chat worker)        ← Move chat agent loop (highest complexity)
  |
Phase 6 (Error handling)     ← Retry policies, timeouts, dead letters
  |
Phase 7 (Dev tooling)        ← Logging, Flower, polish
```

Each phase builds on the previous. Phases 1-3 are foundational. Phase 4 is the lowest-risk
migration. Phase 5 is the biggest change. Phases 6-7 are hardening and polish.
