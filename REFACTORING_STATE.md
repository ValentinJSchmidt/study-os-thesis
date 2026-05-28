# Refactoring State: API/Worker Separation

Last updated: 2026-05-28 (P0 items resolved — see "P0 Resolution" below)

## Overall Status

| Phase | Description | Status | Tests |
|---|---|---|---|
| 1 | Infrastructure (Redis, Celery app, config, utils, publisher) | **Done** | passing |
| 2 | Jobs table & domain (model, service, repository, schemas, controller) | **Done** (migration 0009 generated & applied) | passing |
| 3 | WebSocket layer (manager, listener, controller, lifespan) | **Done** (e2e tests fixed — no longer hang) | passing |
| 4 | Migrate ingestion tasks (theses, chairs, students) | **Done** (tasks now drive the jobs table) | passing |
| 5 | Migrate chat agent loop | **Done** | passing |
| 6 | Retry policies & timeouts | **Done** (incl. dead-letter on exhausted retries) | passing |
| 7 | Regression tests (existing service logic) | **Done** | passing |

**Total: 178 tests, all passing (including the 2 previously-hanging WebSocket e2e tests).**

## P0 Resolution (2026-05-28)

All P0 items from the Gap Analysis below have been fixed and verified end-to-end
against real Postgres + Redis + a live Celery worker:

1. **Double-embedding removed** — `ThesisService.create_thesis(..., embed=False)` and
   `ChairService.create_chair(..., embed=False)` skip inline embedding; the worker does it.
2. **Tasks update the jobs table** — a shared lifecycle runner (`app/worker/task_runner.py`)
   drives `pending → started → success/failure/retry` via `app/worker/job_status.py`.
   Verified: a dispatched task moved a real job row `pending → started → failure`.
3. **`job_id` ordering fixed** — controllers create the job first, dispatch with the real
   `str(job.id)`, then attach `celery_task_id` (`JobService.set_celery_task_id`).
4. **Migration 0009 generated** — `alembic/versions/0009_add_jobs_table.py` (hand-trimmed to
   drop spurious autogen diffs); upgrade/downgrade round-trip verified.
5. **`worker_process_init`** — disposes the inherited engine and rebuilds it with `NullPool`
   so per-task event loops don't share connections (fixes cross-loop asyncpg errors).
6. **WebSocket e2e tests** — controller sends a JSON error before `close()`; tests assert on it.
7. **PDF bytes storage** — `app/students/pdf_store.py` stashes the upload in Redis (1h TTL)
   keyed by job id; the worker fetches/deletes it.

Dead-letter handling (P1 #10) is also done: exhausted retries mark the job `failure`.
Remaining open items: P1 #8 (chat controller private `_chat_repo` access), P1 #9
(per-iteration chat streaming), and the P2 follow-ups (full frontend WS client, integration tests).

## Manual Testing Notes (2026-05-28, local)

Tested end-to-end via `./debug.sh up` on a RAM-constrained dev box (WSL2, ~7.7 GiB).
See [[local-runtime-constraints]] (memory) for the environment limits.

- **Chat — working.** `frontend/src/pages/Chat.tsx` was updated for the async flow:
  `POST .../messages` returns `{job_id}`, the UI polls `GET /api/jobs/{id}` (up to ~5 min)
  and then refetches the conversation. This is an **interim** fix; the intended live
  WebSocket streaming (P2: `frontend/src/api/ws.ts`) is still a follow-up.
- **Transcript upload — failing on this machine (environment, not a code defect).**
  PDF text extraction succeeds, but the LLM extraction step exceeds the task's
  `soft_time_limit` (300s) because the local chat model (`gemma4:e2b`, after the
  `e4b` downgrade) is very slow under memory pressure. The task is killed with
  `SoftTimeLimitExceeded` and the job is correctly marked `failure`. It should work
  on a machine with more RAM (or a smaller/faster extraction model).
  - Minor polish opportunity: `SoftTimeLimitExceeded` is currently caught by the
    generic handler in `app/worker/task_runner.py`; it could be handled explicitly so
    the job `error` reads "timeout" rather than a traceback (TEST_PLAN Phase 6.2 #7).

---

## Test Results

```
tests/unit/   — 151 passed, 0 failed
tests/e2e/    —  20 passed, 0 failed (excluding 2 WebSocket tests)
              —   2 hanging (test_ws_endpoints.py)
```

Run command (excluding hanging tests):

```bash
cd backend
DATABASE_URL="postgresql+asyncpg://test:test@localhost:5433/test" \
JWT_SECRET="test-secret-for-e2e-tests-1234567890" \
uv run pytest tests/ --ignore=tests/e2e/test_ws_endpoints.py -v
```

---

## Known Issues

> **Note (2026-05-28):** The issues in this section have been **resolved** — see
> "P0 Resolution" near the top. The text below is retained as historical context.

### 1. WebSocket e2e tests hang (`tests/e2e/test_ws_endpoints.py`)

**Root cause:** Starlette's sync `TestClient.websocket_connect()` blocks when the
server accepts the connection and then immediately closes it. The ASGI server-side
`websocket.close(code=4001)` sends a close frame, but the test client's
`receive_json()` call blocks forever waiting for data instead of seeing the close.

**Affected tests:**
- `test_websocket_requires_auth` — connects without token, server accepts then closes
- `test_websocket_rejects_invalid_token` — connects with bad JWT, same behavior

**Controller logic is correct** (`app/ws/controller.py`): it accepts, validates the
token, and closes with 4001 if invalid. The issue is purely in how to test this
with Starlette's sync WebSocket test client.

**Fix options:**
1. Use `anyio` with `move_on_after` to add a timeout around the receive call
2. Switch to `httpx-ws` or `websockets` library for the test
3. Have the server send a JSON error message before closing so `receive_json()` returns

### 2. Alembic migration 0009 not yet generated

The `Job` model exists in `app/models/job.py` but the Alembic migration
`0009_add_jobs_table` has not been created yet. Run:

```bash
cd backend
uv run alembic revision --autogenerate -m "add_jobs_table"
uv run alembic upgrade head
```

This is blocked on having the DB container running with the current schema.

### 3. Pre-existing uncommitted changes in working tree

These files have changes **not related** to the API/Worker refactoring:

- `backend/app/models/user.py` — removed `professor` enum value (migration 0008)
- `backend/app/students/schemas.py` — added `model_config = ConfigDict(extra="ignore")`, widened `grade` max_length
- `backend/app/students/service.py` — tweaked LLM prompt wording
- `backend/app/theses/service.py` — (check diff, may be from earlier session)
- `frontend/src/auth/AuthContext.tsx`, `frontend/src/pages/Admin.tsx`, etc. — frontend changes unrelated to this work

---

## Files Created (new)

### Infrastructure (`app/worker/`)

| File | Purpose |
|---|---|
| `app/worker/__init__.py` | Package init |
| `app/worker/celery_app.py` | Celery instance, autodiscover tasks from domain modules |
| `app/worker/celery_config.py` | Broker/backend URLs, serialization, concurrency, retry settings |
| `app/worker/utils.py` | `run_async()` — runs async coroutines inside sync Celery tasks |
| `app/worker/publisher.py` | `publish_event()` — publishes JSON events to Redis Pub/Sub channel `job_events` |

### Jobs domain (`app/jobs/`)

| File | Purpose |
|---|---|
| `app/jobs/__init__.py` | Package init |
| `app/jobs/controller.py` | `GET /api/jobs/{id}`, `GET /api/jobs` endpoints |
| `app/jobs/service.py` | `create_job`, `mark_started`, `mark_success`, `mark_failure`, `mark_retry`, `get_job`, `list_jobs` |
| `app/jobs/repository.py` | CRUD against jobs table (create, get_by_id, update, list_by_user) |
| `app/jobs/schemas.py` | `JobOut` Pydantic schema |
| `app/jobs/deps.py` | `JobServiceDep`, `JobRepoDep` FastAPI DI wiring |
| `app/models/job.py` | `Job` SQLAlchemy model, `JobType` enum, `JobStatus` enum |

### WebSocket layer (`app/ws/`)

| File | Purpose |
|---|---|
| `app/ws/__init__.py` | Package init |
| `app/ws/manager.py` | `ConnectionManager` — tracks WebSocket connections by user_id, dispatches messages |
| `app/ws/listener.py` | `redis_listener()` — subscribes to Redis Pub/Sub, routes events to WebSockets. `_handle_message()` extracted for testability. |
| `app/ws/controller.py` | `WS /api/ws` endpoint — JWT auth via query param, keep-alive loop |

### Celery tasks

| File | Purpose |
|---|---|
| `app/theses/tasks.py` | `embed_thesis` — generates thesis embedding in background |
| `app/chairs/tasks.py` | `ingest_arxiv_paper`, `embed_chair_description` — ArXiv ingestion and chair embedding |
| `app/students/tasks.py` | `parse_transcript` — PDF parsing + LLM extraction + embedding |
| `app/chat/tasks.py` | `process_chat_turn` — full agent loop (up to 6 LLM iterations) with WebSocket event streaming |

### Test files (`tests/`)

| File | Tests | Status |
|---|---|---|
| `tests/conftest.py` | Shared fixtures: `fake_settings`, `mock_llm_chat/embed`, `fake_user/admin`, `_make_orm` | Working |
| `tests/unit/conftest.py` | Mock repositories | Working |
| `tests/e2e/conftest.py` | FastAPI app with DI overrides, Celery patches, `client`/`admin_client` | Working |
| `tests/unit/test_compute_gpa.py` | 10 tests | All passing |
| `tests/unit/test_auth_service.py` | 9 tests | All passing |
| `tests/unit/test_thesis_service.py` | 9 tests | All passing |
| `tests/unit/test_chair_service.py` | 12 tests | All passing |
| `tests/unit/test_student_service.py` | 11 tests | All passing |
| `tests/unit/test_chat_service.py` | 16 tests | All passing |
| `tests/unit/worker/test_celery_config.py` | 9 tests | All passing |
| `tests/unit/worker/test_run_async.py` | 3 tests | All passing |
| `tests/unit/worker/test_publisher.py` | 5 tests | All passing |
| `tests/unit/worker/test_thesis_tasks.py` | 5 tests | All passing |
| `tests/unit/worker/test_chair_tasks.py` | 6 tests | All passing |
| `tests/unit/worker/test_student_tasks.py` | 5 tests | All passing |
| `tests/unit/worker/test_chat_tasks.py` | 6 tests | All passing |
| `tests/unit/worker/test_retry_policy.py` | 10 tests | All passing |
| `tests/unit/ws/test_connection_manager.py` | 8 tests | All passing |
| `tests/unit/ws/test_listener.py` | 4 tests | All passing |
| `tests/unit/jobs/test_job_schemas.py` | 5 tests | All passing |
| `tests/unit/jobs/test_job_service.py` | 14 tests | All passing |
| `tests/e2e/test_health.py` | 1 test | Passing |
| `tests/e2e/test_job_endpoints.py` | 5 tests | All passing |
| `tests/e2e/test_thesis_endpoints.py` | 6 tests | All passing |
| `tests/e2e/test_chair_endpoints.py` | 4 tests | All passing |
| `tests/e2e/test_student_endpoints.py` | 3 tests | All passing |
| `tests/e2e/test_chat_endpoints.py` | 5 tests | All passing |
| `tests/e2e/test_ws_endpoints.py` | 2 tests | **Hanging** |

---

## Files Modified (existing)

| File | Changes |
|---|---|
| `docker-compose.yml` | Added `redis` service (redis:7-alpine, port 6379, healthcheck, noeviction, AOF) and `redis-data` volume |
| `backend/pyproject.toml` | Added `celery[redis]>=5.4`, `redis>=5.0` to deps; `pytest-cov`, `respx` to dev deps; `asyncio_mode = "auto"`, markers, `tests/**/*.py` ANN ignore |
| `backend/app/config.py` | Added `redis_url` field with alias `REDIS_URL` |
| `backend/.env.example` | Added `REDIS_URL=redis://localhost:6379/0` |
| `backend/app/models/__init__.py` | Re-exports `Job`, `JobType`, `JobStatus` |
| `backend/app/main.py` | Imports+registers `jobs_router`, `ws_router`; lifespan creates `ConnectionManager`, starts `redis_listener` asyncio task, cancels on shutdown |
| `backend/app/theses/controller.py` | `POST /` now creates thesis (no embedding), dispatches `embed_thesis.delay()`, returns `{...thesis, job_id}` with 201 |
| `backend/app/chairs/controller.py` | `POST /` dispatches `embed_chair_description.delay()`, returns `{...chair, job_id}` with 201. `POST /{id}/documents/arxiv` validates chair exists, dispatches `ingest_arxiv_paper.delay()`, returns `{job_id}` with 202 |
| `backend/app/students/controller.py` | `POST /me/transcript` validates PDF, dispatches `parse_transcript.delay()`, returns `{job_id}` with 202. No longer calls service inline. |
| `backend/app/chat/controller.py` | `POST /sessions/{id}/messages` validates session ownership, dispatches `process_chat_turn.delay()`, returns `{job_id, session_id}` with 202 |
| `debug.sh` | Launches Celery worker (`uv run celery -A app.worker.celery_app worker`) as third background process. Added `CELERY_PID`, `redis_is_healthy()`, Redis health check in `cmd_start`/`cmd_up`. |

---

## What Still Needs to Be Done

### Blocking (must fix before merge)

1. **Fix WebSocket e2e tests** — either change the test approach (use `anyio.move_on_after` timeout, or send a JSON error before closing) or change the controller to send an error message before closing so `receive_json()` returns.

2. **Generate Alembic migration 0009** — `alembic revision --autogenerate -m "add_jobs_table"` then `alembic upgrade head`.

### Non-blocking (can be follow-up PRs)

3. **Integration tests** — `tests/integration/` directory exists but has no test files. Needs a test DB fixture and repository-level tests against real PostgreSQL+pgvector.

4. **PDF bytes storage for transcript worker** — The `parse_transcript` task currently receives a placeholder `pdf_bytes_ref`. In production the PDF bytes need to be stored (e.g. in Redis, S3, or a temp file) and referenced by key so the worker can retrieve them.

5. **Chat WebSocket streaming** — The `process_chat_turn` task publishes `chat_turn_started` and `chat_turn_completed` events, but does not yet publish intermediate `chat_message` or `chat_tool_call` events after each LLM iteration. The service layer needs hooks to publish per-iteration.

6. **Frontend WebSocket client** — `frontend/src/api/ws.ts` and Chat page updates for real-time message streaming.

7. **Flower monitoring dashboard** — Optional. Add `flower` to dev deps and a command in `debug.sh`.

8. **ThesisService.create_thesis still calls embed inline** — The controller dispatches to a Celery task, but the service method itself still calls `self._ollama.embed(...)`. The service should be refactored to optionally skip embedding (or a new `create_thesis_without_embedding` method) so the controller can persist the thesis row without an embedding, then the worker generates it. Currently the e2e test works because the service is fully mocked, but in a real integration test this would double-embed.

---

## Architecture Diagram (Post-Refactor)

```
                 ┌──────────────┐
                 │   Frontend   │
                 │  (React/TS)  │
                 └──────┬───────┘
                        │ HTTP + WebSocket
                        ▼
                 ┌──────────────┐
                 │  FastAPI API  │
                 │   (uvicorn)   │
                 │               │
                 │ • Auth/CRUD   │ ◄──── Redis Pub/Sub ◄───┐
                 │ • Job create  │       (listener)         │
                 │ • WS push     │                          │
                 └──────┬───────┘                          │
                        │ .delay()                          │
                        ▼                                   │
                 ┌──────────────┐                          │
                 │  Redis 7     │                          │
                 │  (broker +   │                          │
                 │   pub/sub)   │                          │
                 └──────┬───────┘                          │
                        │ task queue                        │
                        ▼                                   │
                 ┌──────────────┐                          │
                 │ Celery Worker │──── publish_event() ────┘
                 │               │
                 │ • embed_thesis│
                 │ • ingest_arxiv│
                 │ • parse_trans │
                 │ • chat_turn   │
                 └──────┬───────┘
                        │ asyncio.run()
                        ▼
                 ┌──────────────┐     ┌──────────────┐
                 │ PostgreSQL   │     │ Ollama / LLM │
                 │  + pgvector  │     │  (chat/embed) │
                 └──────────────┘     └──────────────┘
```

---

## Gap Analysis: What Remains to Complete the Implementation Plan

This section is self-contained. An agent reading only this file and the codebase
can pick up the work and finish it without needing prior conversation context.

### How to orient

- `IMPLEMENTATION_PLAN.md` — the full design specification (7 phases)
- `TEST_PLAN.md` — the TDD test specifications (173 tests)
- `backend/tests/` — the implemented tests (run with `uv run pytest tests/ --ignore=tests/e2e/test_ws_endpoints.py -v` from `backend/`)
- This file — current state, what's done, what's broken, what's missing
- All source lives under `backend/app/`. The stack is FastAPI + SQLAlchemy async + Celery + Redis + PostgreSQL/pgvector.

Set env vars before running tests:
```bash
export DATABASE_URL="postgresql+asyncpg://test:test@localhost:5433/test"
export JWT_SECRET="test-secret-for-e2e-tests-1234567890"
```

### P0 — Must fix (blocks correct runtime behavior)

#### 1. Services still embed inline — double-embedding bug

**Problem:** The controllers now dispatch Celery tasks for embedding, but the
service methods they call still perform embedding synchronously before returning.
This means every create operation embeds twice: once inline (service), once in the
worker (task).

**Files to fix:**
- `app/theses/service.py` — `create_thesis()` calls `self._ollama.embed(...)` on
  line 33. The plan says: "persist thesis (embedding=None) -> dispatch task."
  Add an `embedding: list[float] | None = None` parameter or a `skip_embedding=True`
  flag so the controller can persist without embedding. The existing unit tests in
  `tests/unit/test_thesis_service.py` test the current inline behavior and will need
  updating — the `test_embeds_title_and_abstract` test should verify the service
  *can* skip embedding when told to.
- `app/chairs/service.py` — `create_chair()` calls `self._embed_text(...)` on line 46.
  Same issue: the controller dispatches `embed_chair_description.delay()` but the
  service also embeds inline. Refactor similarly.

#### 2. Tasks don't update the `jobs` table

**Problem:** All four Celery tasks accept a `job_id` parameter and publish Redis
Pub/Sub events, but never call `JobService.mark_started()`, `mark_success()`, or
`mark_failure()`. The `jobs` table rows stay in `pending` status forever.

**Files to fix:** `app/theses/tasks.py`, `app/chairs/tasks.py`,
`app/students/tasks.py`, `app/chat/tasks.py`.

Each task body should:
1. Call `job_service.mark_started(job_id)` at the top
2. Call `job_service.mark_success(job_id, result_data={...})` on success
3. Call `job_service.mark_failure(job_id, error=traceback_str)` on permanent failure
4. Call `job_service.mark_retry(job_id)` before `self.retry(exc=exc)`

The `_get_deps()` function already builds a `JobService` — it just isn't used.

#### 3. `job_id` ordering is wrong — task doesn't know the real UUID

**Problem:** The controllers call `.delay()` first, then `job_service.create_job()`
second. The task receives `job_id="pending"` as a string literal, not the real UUID.

**Fix:** Reverse the order in every controller:
```python
# WRONG (current):
task_result = embed_thesis.delay(thesis_id, user_id, "pending")
job = await job_service.create_job(..., celery_task_id=task_result.id)

# CORRECT:
job = await job_service.create_job(..., celery_task_id=None)
task_result = embed_thesis.delay(thesis_id, user_id, str(job.id))
# Optionally update job.celery_task_id = task_result.id
```

**Affected files:** `app/theses/controller.py`, `app/chairs/controller.py`,
`app/students/controller.py`, `app/chat/controller.py`.

#### 4. Alembic migration 0009 not generated

The `Job` model exists in `app/models/job.py` but there is no migration file.
Run from `backend/`:
```bash
uv run alembic revision --autogenerate -m "add_jobs_table"
```
Then verify the generated migration and run `uv run alembic upgrade head`.

#### 5. `worker_process_init` signal handler missing

The plan specifies disposing the inherited SQLAlchemy engine after Celery forks.
Without this, `asyncpg` connections inherited across fork will cause errors.

Add to `app/worker/celery_app.py`:
```python
from celery.signals import worker_process_init

@worker_process_init.connect
def on_worker_init(**kwargs):
    import asyncio
    from app.db import engine
    asyncio.run(engine.dispose())
```

#### 6. WebSocket e2e tests hang

`tests/e2e/test_ws_endpoints.py` has 2 tests that block forever. The WS controller
accepts the connection then closes with code 4001. Starlette's sync `TestClient`
blocks on `receive_json()` because it doesn't treat the close frame as an exception.

**Recommended fix:** Have the controller send a JSON error payload *before* closing:
```python
await websocket.send_json({"error": "Missing token"})
await websocket.close(code=4001)
```
Then the test's `receive_json()` returns the error dict and the test can assert on it
without hanging. Update both `test_websocket_requires_auth` and
`test_websocket_rejects_invalid_token` to assert on the received error payload.

#### 7. PDF bytes storage for transcript worker

`app/students/controller.py` passes `pdf_bytes_ref="inline"` — a placeholder. The
actual PDF bytes from the upload are lost after the HTTP response. The task has no
way to retrieve them.

**Fix options (pick one):**
- Store bytes in Redis with a TTL: `redis.set(f"pdf:{job_id}", pdf_bytes, ex=3600)`
  and have the task `redis.get(f"pdf:{job_id}")`.
- Write to a temp file under a known path and pass the path as `pdf_bytes_ref`.
- Store in PostgreSQL as a `BYTEA` column on the `jobs` table's `input_data` (not
  recommended for large files).

### P1 — Should fix (code quality / correctness)

#### 8. Chat controller accesses private `_chat_repo`

`app/chat/controller.py` line 54: `chat_service._chat_repo.get_session(session_id)`.
This breaks the service abstraction. Add a public method to `ChatService`:
```python
async def validate_session_ownership(self, session_id: int, user_id: int) -> None:
```

#### 9. Per-iteration event publishing in chat service

The plan (Phase 5.1, 5.2) specifies publishing `chat_message` and `chat_tool_call`
events after each LLM iteration so the frontend sees messages in real-time. Currently
only `chat_turn_started` and `chat_turn_completed` bookend events are published.

**Fix:** The `ChatService._run_agent_turn()` method needs to accept an optional
callback/publisher. The `process_chat_turn` task would pass a lambda that calls
`publish_event(...)`. After each `create_message` call inside the agent loop, invoke
the callback.

#### 10. Dead letter handling (Phase 6.3)

Tasks that exhaust `max_retries` should update `job.status = failure` in the DB.
Currently nothing catches `MaxRetriesExceededError`. Use Celery's `on_failure`
handler or a `try/except` around `self.retry()`:
```python
except (ConnectionError, TimeoutError) as exc:
    try:
        raise self.retry(exc=exc)
    except self.MaxRetriesExceededError:
        run_async(job_service.mark_failure(job_id, f"Exhausted retries: {exc}"))
        publish_event(..., event_type="task_failed", status="failure")
        raise
```

### P2 — Follow-up PRs (not blocking backend correctness)

| Item | Description |
|---|---|
| Frontend WebSocket client | Create `frontend/src/api/ws.ts` — connect to `/api/ws?token=...`, dispatch received events |
| Frontend Chat.tsx streaming | Listen for `chat_message` events, render messages as they arrive instead of waiting for HTTP response |
| Celery worker logging | Configure `--logfile=logs/celery.log` and/or integrate with `log_config.json` |
| Flower dashboard | Add `flower` to dev deps, add launch command to `debug.sh` |
| Integration tests | `tests/integration/` is empty. Write repository-level tests against real PostgreSQL+pgvector |

### Verification: how to confirm everything works

After completing all P0 items, run:
```bash
cd backend

# All unit + e2e tests should pass (173 total, 0 hanging)
uv run pytest tests/ -v

# Start infra and verify end-to-end manually
cd .. && ./debug.sh up
# In another terminal:
curl -X POST http://localhost:8000/api/auth/login -d '{"email":"...","password":"..."}'
# Use the token to create a thesis, check /api/jobs/{id}, connect to ws://localhost:8000/api/ws?token=...
```
