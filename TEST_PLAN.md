# Test Plan: API/Worker Separation (TDD)

This document specifies every test to be written **before** the corresponding implementation.
Tests are organized by phase (matching `IMPLEMENTATION_PLAN.md`) and by layer (unit,
integration, e2e). Each test table includes the test name, what it asserts, and its pytest
marker.

---

## Table of Contents

- [Phase 0 -- Test Infrastructure](#phase-0----test-infrastructure)
- [Phase 1 -- Celery + Redis](#phase-1----celery--redis)
- [Phase 2 -- Jobs Table & Domain](#phase-2----jobs-table--domain)
- [Phase 3 -- WebSocket Layer](#phase-3----websocket-layer)
- [Phase 4 -- Ingestion Tasks](#phase-4----ingestion-tasks)
- [Phase 5 -- Chat Worker](#phase-5----chat-worker)
- [Phase 6 -- Error Handling & Retries](#phase-6----error-handling--retries)
- [Phase 7 -- Regression Tests (Existing Code)](#phase-7----regression-tests-existing-code)
- [Test Count Summary](#test-count-summary)
- [Execution Order](#execution-order)
- [Running Tests](#running-tests)

---

## Phase 0 -- Test Infrastructure

### 0.1 Pytest Configuration

Update `backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "unit: fast, no I/O, all deps mocked",
    "integration: requires PostgreSQL + pgvector",
    "e2e: full HTTP stack with DI overrides",
]
```

New dev dependencies:

```toml
[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
    "respx>=0.22",
    "ruff>=0.6",
]
```

### 0.2 Directory Layout

```
backend/tests/
├── conftest.py                        # Shared fixtures
├── factories.py                       # Test data helpers
│
├── unit/
│   ├── conftest.py                    # Unit-specific fixtures (mock repos)
│   ├── test_compute_gpa.py
│   ├── test_thesis_service.py
│   ├── test_chair_service.py
│   ├── test_student_service.py
│   ├── test_chat_service.py
│   ├── test_auth_service.py
│   │
│   ├── worker/
│   │   ├── test_celery_config.py
│   │   ├── test_run_async.py
│   │   ├── test_publisher.py
│   │   ├── test_thesis_tasks.py
│   │   ├── test_chair_tasks.py
│   │   ├── test_student_tasks.py
│   │   └── test_chat_tasks.py
│   │
│   ├── ws/
│   │   ├── test_connection_manager.py
│   │   └── test_listener.py
│   │
│   └── jobs/
│       ├── test_job_service.py
│       └── test_job_schemas.py
│
├── integration/
│   ├── conftest.py                    # DB engine, session, table lifecycle
│   ├── test_thesis_repository.py
│   ├── test_chair_repository.py
│   ├── test_student_repository.py
│   ├── test_chat_repository.py
│   ├── test_job_repository.py
│   └── test_pdf_extraction.py
│
├── e2e/
│   ├── conftest.py                    # FastAPI TestClient, DI overrides
│   ├── test_thesis_endpoints.py
│   ├── test_chair_endpoints.py
│   ├── test_student_endpoints.py
│   ├── test_chat_endpoints.py
│   ├── test_job_endpoints.py
│   ├── test_ws_endpoints.py
│   └── test_health.py
│
└── fixtures/
    └── sample_transcript.pdf
```

### 0.3 Shared Fixtures (`tests/conftest.py`)

| Fixture | Scope | Provides |
|---|---|---|
| `fake_settings` | session | `Settings` with test-safe values (dummy DB URL, test JWT secret, localhost Ollama) |
| `mock_llm_chat` | function | `AsyncMock` satisfying `LLMPort` -- `chat` returns `{"message": {"role": "assistant", "content": "Hello!", "tool_calls": []}}` |
| `mock_llm_embed` | function | `AsyncMock` satisfying `LLMPort` -- `embed` returns `[0.1] * 2560` |
| `fake_user` | function | `User(id=1, email="student@test.com", role=student, password_hash="x")` |
| `fake_admin` | function | `User(id=2, email="admin@test.com", role=admin, password_hash="x")` |
| `embedding_dim` | session | `2560` |

### 0.4 Integration Fixtures (`tests/integration/conftest.py`)

| Fixture | Scope | Provides |
|---|---|---|
| `db_engine` | session | `AsyncEngine` from env `TEST_DATABASE_URL` (PostgreSQL + pgvector) |
| `db_tables` | session | `create_all` on setup, `drop_all` on teardown |
| `db_session` | function | `AsyncSession` wrapped in a savepoint; rolled back after each test |

### 0.5 E2E Fixtures (`tests/e2e/conftest.py`)

| Fixture | Scope | Provides |
|---|---|---|
| `app` | session | `FastAPI` app with `dependency_overrides`: mock `get_session`, `get_current_user`, LLM clients |
| `client` | function | `httpx.AsyncClient(transport=ASGITransport(app))` -- student user |
| `admin_client` | function | Same but `get_current_user` → `fake_admin` |

---

## Phase 1 -- Celery + Redis

### `tests/unit/worker/test_celery_config.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_broker_url_uses_redis` | `broker_url` starts with `"redis://"` | unit |
| 2 | `test_result_backend_uses_redis` | `result_backend` starts with `"redis://"` | unit |
| 3 | `test_task_serializer_is_json` | `task_serializer == "json"` | unit |
| 4 | `test_result_serializer_is_json` | `result_serializer == "json"` | unit |
| 5 | `test_task_acks_late_enabled` | `task_acks_late is True` | unit |
| 6 | `test_task_track_started_enabled` | `task_track_started is True` | unit |
| 7 | `test_worker_prefetch_multiplier_is_one` | `worker_prefetch_multiplier == 1` | unit |
| 8 | `test_task_reject_on_worker_lost_enabled` | `task_reject_on_worker_lost is True` | unit |
| 9 | `test_result_expires_is_24h` | `result_expires == 86400` | unit |

### `tests/unit/worker/test_run_async.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_run_async_returns_coroutine_result` | Coroutine returning `42` → `run_async` returns `42` | unit |
| 2 | `test_run_async_propagates_exception` | Coroutine raising `ValueError("boom")` → `run_async` raises `ValueError` | unit |
| 3 | `test_run_async_works_consecutively` | Two consecutive `run_async` calls succeed (no "loop already running" error) | unit |

---

## Phase 2 -- Jobs Table & Domain

### `tests/unit/jobs/test_job_schemas.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_job_type_enum_has_all_values` | `JobType` contains `embed_thesis`, `embed_chair`, `ingest_arxiv`, `parse_transcript`, `chat_turn`, `generate_proposal` | unit |
| 2 | `test_job_status_enum_has_all_values` | `JobStatus` contains `pending`, `started`, `success`, `failure`, `retry` | unit |
| 3 | `test_job_out_serializes_from_orm` | `JobOut.model_validate(fake_job)` produces dict with all expected fields | unit |
| 4 | `test_job_out_includes_timestamps` | Serialized output has `created_at`, `started_at`, `completed_at` | unit |
| 5 | `test_job_out_id_is_string_uuid` | `id` field serializes as a UUID string | unit |

### `tests/unit/jobs/test_job_service.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_create_job_sets_pending_status` | Returned job has `status == JobStatus.pending` | unit |
| 2 | `test_create_job_stores_input_data` | `job.input_data == {"thesis_id": 5}` | unit |
| 3 | `test_create_job_assigns_user_id` | `job.user_id == 1` | unit |
| 4 | `test_create_job_stores_celery_task_id` | `job.celery_task_id == "abc-123"` | unit |
| 5 | `test_mark_started_updates_status_and_timestamp` | `status == started`, `started_at is not None` | unit |
| 6 | `test_mark_success_sets_result_and_completed_at` | `status == success`, `result_data == {...}`, `completed_at is not None` | unit |
| 7 | `test_mark_failure_stores_error` | `status == failure`, `error == "traceback..."`, `completed_at is not None` | unit |
| 8 | `test_mark_retry_increments_attempts` | `attempts == 1`, `status == retry` | unit |
| 9 | `test_get_job_returns_job_for_owner` | Returns job when `user_id` matches | unit |
| 10 | `test_get_job_raises_not_found_for_wrong_user` | `NotFoundException` when user_id doesn't match | unit |
| 11 | `test_get_job_raises_not_found_for_missing_id` | `NotFoundException` for nonexistent UUID | unit |
| 12 | `test_list_jobs_returns_only_user_jobs` | Filters by `user_id` | unit |
| 13 | `test_list_jobs_filters_by_type` | `type=embed_thesis` returns only matching jobs | unit |
| 14 | `test_list_jobs_filters_by_status` | `status=pending` returns only matching jobs | unit |

### `tests/integration/test_job_repository.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_create_and_retrieve_job` | Job round-trips through PostgreSQL with all fields intact | integration |
| 2 | `test_job_id_is_auto_generated_uuid` | `job.id` is a `uuid.UUID` instance | integration |
| 3 | `test_update_job_status_persists` | Status change is visible after commit + re-fetch | integration |
| 4 | `test_list_jobs_by_user_id` | Only returns jobs with matching `user_id` | integration |
| 5 | `test_input_data_jsonb_round_trips` | `{"key": [1, 2, {"nested": true}]}` survives JSONB serialization | integration |
| 6 | `test_created_at_has_server_default` | `created_at` is populated even when not explicitly set | integration |

### `tests/e2e/test_job_endpoints.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_get_job_200` | `GET /api/jobs/{id}` → 200 with `status`, `type`, `created_at` fields | e2e |
| 2 | `test_get_job_not_found_404` | `GET /api/jobs/{random_uuid}` → 404 | e2e |
| 3 | `test_list_jobs_returns_own_jobs` | `GET /api/jobs` → 200, only current user's jobs in response | e2e |
| 4 | `test_list_jobs_filter_by_type` | `GET /api/jobs?type=embed_thesis` → filtered results | e2e |
| 5 | `test_list_jobs_filter_by_status` | `GET /api/jobs?status=pending` → filtered results | e2e |
| 6 | `test_get_job_forbidden_for_other_user` | Job owned by user A → user B gets 404 | e2e |

### Alembic Migration

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_alembic_upgrade_head` | `alembic upgrade head` succeeds on empty test DB | integration |
| 2 | `test_alembic_downgrade_removes_jobs` | Downgrade from 0009 → 0008 drops the `jobs` table | integration |

---

## Phase 3 -- WebSocket Layer

### `tests/unit/ws/test_connection_manager.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_connect_registers_websocket` | After `connect(user_id=1, ws)`, manager tracks the connection | unit |
| 2 | `test_disconnect_removes_websocket` | After `disconnect(1, ws)`, connection no longer tracked | unit |
| 3 | `test_disconnect_unknown_is_noop` | Disconnecting an unregistered WebSocket does not raise | unit |
| 4 | `test_send_to_user_calls_send_json` | `send_to_user(1, data)` calls `ws.send_json(data)` exactly once | unit |
| 5 | `test_send_to_user_no_connections_is_noop` | Sending to user with no connections does not raise | unit |
| 6 | `test_multiple_connections_per_user` | Two WebSockets for same user → both receive the message | unit |
| 7 | `test_stale_connection_does_not_crash` | `ws.send_json` raising `RuntimeError` → skipped, no exception propagated | unit |
| 8 | `test_send_to_wrong_user_delivers_nothing` | `send_to_user(user_id=2, ...)` does not call send on user 1's WebSocket | unit |

### `tests/unit/ws/test_listener.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_dispatches_message_to_manager` | Valid Redis message → `manager.send_to_user` called with correct `user_id` and data | unit |
| 2 | `test_ignores_subscribe_messages` | Redis message with `type="subscribe"` → `send_to_user` not called | unit |
| 3 | `test_handles_malformed_json` | Invalid JSON payload → logged, `send_to_user` not called, no crash | unit |
| 4 | `test_handles_missing_user_id` | JSON without `user_id` key → skipped gracefully | unit |

### `tests/unit/worker/test_publisher.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_publishes_to_job_events_channel` | `redis.publish` called with channel `"job_events"` | unit |
| 2 | `test_payload_is_valid_json` | Published bytes decode to JSON with `type`, `job_id`, `user_id`, `status` keys | unit |
| 3 | `test_payload_includes_iso_timestamp` | `timestamp` field is a valid ISO 8601 string | unit |
| 4 | `test_payload_includes_data_dict` | `data` field contains the passed dict | unit |
| 5 | `test_redis_error_does_not_raise` | `redis.publish` raising `ConnectionError` → function returns without raising, logs warning | unit |

### `tests/e2e/test_ws_endpoints.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_websocket_connect_succeeds` | Client connects to `/api/ws` and receives ack | e2e |
| 2 | `test_websocket_receives_job_event` | Publish Redis event for connected user → client receives it | e2e |
| 3 | `test_websocket_ignores_other_user_events` | Event for user 2 → user 1's WebSocket receives nothing | e2e |
| 4 | `test_websocket_requires_auth` | Connection without token → rejected (403 or close) | e2e |
| 5 | `test_websocket_disconnect_cleans_up` | After disconnect, manager no longer holds the connection | e2e |

---

## Phase 4 -- Ingestion Tasks

### 4.1 Thesis Embedding

#### `tests/unit/worker/test_thesis_tasks.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_embed_thesis_calls_embed_with_title_and_abstract` | `LLMPort.embed` called with `"{title}\n\n{abstract}"` | unit |
| 2 | `test_embed_thesis_updates_thesis_embedding` | Thesis row's `embedding` field is set after task completes | unit |
| 3 | `test_embed_thesis_marks_job_started` | Job status transitions to `started` at beginning of task | unit |
| 4 | `test_embed_thesis_marks_job_success` | Job status is `success` after completion | unit |
| 5 | `test_embed_thesis_marks_job_failure_on_error` | LLM error → `job.status == failure`, `job.error` is set | unit |
| 6 | `test_embed_thesis_publishes_success_event` | `publish_event` called with `event_type="task_complete"` | unit |
| 7 | `test_embed_thesis_publishes_failure_event` | On error → `publish_event` called with `event_type="task_failed"` | unit |
| 8 | `test_embed_thesis_retries_on_connection_error` | `ConnectionError` → `self.retry(exc=exc)` called | unit |
| 9 | `test_embed_thesis_no_retry_on_not_found` | `NotFoundException` → fails immediately, no retry | unit |

#### `tests/e2e/test_thesis_endpoints.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_create_thesis_returns_201_with_job_id` | Response has `thesis` and `job_id` fields | e2e |
| 2 | `test_create_thesis_stores_thesis_without_embedding` | Thesis persisted with `embedding is None` | e2e |
| 3 | `test_create_thesis_dispatches_celery_task` | Celery `.delay()` called with thesis_id | e2e |
| 4 | `test_create_thesis_validates_title_min_length` | `title=""` → 422 | e2e |
| 5 | `test_create_thesis_validates_abstract_min_length` | `abstract="short"` → 422 | e2e |
| 6 | `test_create_thesis_requires_admin_role` | Student user → 403 | e2e |
| 7 | `test_get_thesis_works_without_embedding` | `GET /api/theses/{id}` returns thesis even if embedding is null | e2e |
| 8 | `test_list_theses_returns_list` | `GET /api/theses` → 200 with list | e2e |

### 4.2 ArXiv Ingestion

#### `tests/unit/worker/test_chair_tasks.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_ingest_arxiv_calls_fetch_metadata` | `_fetch_arxiv_metadata(arxiv_id)` called | unit |
| 2 | `test_ingest_arxiv_embeds_abstract` | `LLMPort.embed` called with abstract text | unit |
| 3 | `test_ingest_arxiv_stores_paper_document` | `ChairRepository.add_document` called with `kind=paper`, correct title, content, embedding | unit |
| 4 | `test_ingest_arxiv_marks_job_success` | `job.status == success` | unit |
| 5 | `test_ingest_arxiv_duplicate_fails_permanently` | `AlreadyExistsException` → job fails, no retry | unit |
| 6 | `test_ingest_arxiv_retries_on_network_error` | `httpx.ConnectError` → retry | unit |
| 7 | `test_ingest_arxiv_publishes_event` | `publish_event` called on completion | unit |
| 8 | `test_embed_chair_description_embeds_text` | `LLMPort.embed` called with `short_description` | unit |
| 9 | `test_embed_chair_description_stores_description_document` | `add_document(kind=description, ...)` called | unit |
| 10 | `test_embed_chair_description_marks_job_success` | Job succeeds | unit |

#### `tests/e2e/test_chair_endpoints.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_ingest_arxiv_returns_202_with_job_id` | `POST /api/chairs/{id}/documents/arxiv` → 202 with `job_id` | e2e |
| 2 | `test_ingest_arxiv_validates_arxiv_id` | `arxiv_id=""` → 422 | e2e |
| 3 | `test_ingest_arxiv_chair_not_found` | Invalid `chair_id` → 404 | e2e |
| 4 | `test_create_chair_returns_chair_and_job_id` | `POST /api/chairs` → chair data + `job_id` for embedding | e2e |
| 5 | `test_create_chair_stores_chair_immediately` | Chair row exists before embedding task completes | e2e |
| 6 | `test_list_chairs_returns_list` | `GET /api/chairs` → 200 | e2e |
| 7 | `test_delete_chair_returns_204` | `DELETE /api/chairs/{id}` → 204 | e2e |

### 4.3 Transcript Upload

#### `tests/unit/worker/test_student_tasks.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_parse_transcript_calls_extract_pdf_text` | `_extract_pdf_text` called with stored PDF bytes | unit |
| 2 | `test_parse_transcript_calls_llm_with_json_format` | `LLMPort.chat` called with `format="json"` and transcript prompt | unit |
| 3 | `test_parse_transcript_computes_gpa` | GPA from `[{grade: "1,3", credits: 5}, {grade: "2,0", credits: 3}]` → correct weighted average | unit |
| 4 | `test_parse_transcript_embeds_course_profile` | `LLMPort.embed` called with concatenated course names | unit |
| 5 | `test_parse_transcript_upserts_student` | `StudentRepository.upsert` called with gpa, courses, embedding | unit |
| 6 | `test_parse_transcript_marks_job_success` | `job.status == success`, `result_data` has course count | unit |
| 7 | `test_parse_transcript_invalid_llm_json_fails` | LLM returns `"not json"` → job fails with descriptive error | unit |
| 8 | `test_parse_transcript_empty_pdf_fails` | Empty extracted text → job fails with "no text extracted" | unit |
| 9 | `test_parse_transcript_retries_on_llm_timeout` | LLM timeout → retry | unit |
| 10 | `test_parse_transcript_publishes_event` | `publish_event` called | unit |

#### `tests/e2e/test_student_endpoints.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_upload_transcript_returns_202_with_job_id` | `POST /api/students/me/transcript` → 202 with `job_id` | e2e |
| 2 | `test_upload_transcript_rejects_non_pdf` | `Content-Type: text/plain` → 400 | e2e |
| 3 | `test_upload_transcript_rejects_oversize_file` | >10 MB → 400 | e2e |
| 4 | `test_get_profile_works_before_transcript` | `GET /api/students/me` works even with no transcript job completed | e2e |

---

## Phase 5 -- Chat Worker

### 5.1 Chat Task

#### `tests/unit/worker/test_chat_tasks.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_chat_turn_loads_history` | `ChatRepository.list_messages(session_id)` called | unit |
| 2 | `test_chat_turn_calls_llm_with_system_prompt` | First message in LLM call has `role=system` | unit |
| 3 | `test_chat_turn_no_tool_calls` | LLM returns content, no tool_calls → single assistant message persisted, job succeeds | unit |
| 4 | `test_chat_turn_single_tool_call_iteration` | LLM returns tool_call → tool executed → second LLM call → final message | unit |
| 5 | `test_chat_turn_three_tool_iterations` | Agent loop runs 3 times before returning final answer | unit |
| 6 | `test_chat_turn_max_iterations_stops` | After 6 iterations of tool calls, loop stops with limit message | unit |
| 7 | `test_chat_turn_publishes_turn_started` | `chat_turn_started` event published at beginning | unit |
| 8 | `test_chat_turn_publishes_each_assistant_message` | After each LLM response, `chat_message` event published via Redis | unit |
| 9 | `test_chat_turn_publishes_tool_call_event` | When tool invoked, `chat_tool_call` event published with `tool_name` | unit |
| 10 | `test_chat_turn_publishes_turn_completed` | `chat_turn_completed` event published at end | unit |
| 11 | `test_chat_turn_marks_job_success` | `job.status == success` on normal completion | unit |
| 12 | `test_chat_turn_marks_job_failure_on_llm_error` | LLM raises → `job.status == failure` | unit |
| 13 | `test_chat_turn_retries_on_connection_error` | Network error → Celery retry | unit |
| 14 | `test_chat_turn_persists_all_messages` | User, assistant, and tool messages all saved to `chat_messages` | unit |
| 15 | `test_chat_turn_includes_student_context` | Student with courses → system prompt includes GPA and course names | unit |
| 16 | `test_chat_turn_no_student_context` | No student record → system prompt has no student section | unit |

### 5.2 Tool Execution (unit, in `tests/unit/test_chat_service.py`)

These extend the existing chat service tests to cover tool dispatch:

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_tool_search_theses_calls_embed_and_search` | `embed` called with query, `search_theses_with_client` called | unit |
| 2 | `test_tool_search_chairs_calls_embed_and_repo` | `embed` called, `ChairRepository.search_by_embedding` called | unit |
| 3 | `test_tool_generate_proposal_calls_llm` | `LLMPort.chat` called with generation prompt | unit |
| 4 | `test_tool_generate_proposal_embeds_each_proposal` | `embed` called once per generated proposal | unit |
| 5 | `test_tool_generate_proposal_creates_thesis_rows` | Thesis rows created with `source=student`, `generated_for_user_id` set | unit |
| 6 | `test_tool_unknown_name_returns_error_json` | Unknown tool → returns JSON error string, no exception | unit |
| 7 | `test_tool_search_theses_handles_embed_failure` | Embed raises → tool returns error message | unit |

### 5.3 Chat Controller (e2e)

#### `tests/e2e/test_chat_endpoints.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_send_message_returns_202_with_job_id` | `POST /api/chat/sessions/{id}/messages` → 202, body has `job_id` and `message_id` | e2e |
| 2 | `test_send_message_persists_user_message` | User message visible via `GET .../messages` immediately | e2e |
| 3 | `test_send_message_dispatches_celery_task` | Celery `.delay()` called with `(session_id, user_id, content)` | e2e |
| 4 | `test_send_message_validates_content_min` | `content=""` → 422 | e2e |
| 5 | `test_send_message_validates_content_max` | `content` > 4000 chars → 422 | e2e |
| 6 | `test_send_message_session_not_found` | Bad session_id → 404 | e2e |
| 7 | `test_send_message_wrong_user` | User A posting to User B's session → 404 or 403 | e2e |
| 8 | `test_create_session_returns_session` | `POST /api/chat/sessions` → 201 with session object | e2e |
| 9 | `test_list_sessions_returns_list` | `GET /api/chat/sessions` → 200 with list | e2e |
| 10 | `test_get_messages_returns_all` | `GET /api/chat/sessions/{id}/messages` returns user + assistant + tool messages | e2e |

---

## Phase 6 -- Error Handling & Retries

These tests are spread across the per-task test files but are listed here as a consolidated
specification for the retry and timeout contracts.

### 6.1 Retry Policy Verification

| # | Test | Task(s) | Asserts | Marker |
|---|---|---|---|---|
| 1 | `test_embed_thesis_max_retries` | `embed_thesis` | `task.max_retries == 3` | unit |
| 2 | `test_ingest_arxiv_max_retries` | `ingest_arxiv` | `task.max_retries == 3` | unit |
| 3 | `test_parse_transcript_max_retries` | `parse_transcript` | `task.max_retries == 3` | unit |
| 4 | `test_chat_turn_max_retries` | `process_chat_turn` | `task.max_retries == 2` | unit |
| 5 | `test_connection_error_triggers_retry` | all | `ConnectionError` → `self.retry()` called | unit |
| 6 | `test_timeout_error_triggers_retry` | all | `TimeoutError` → `self.retry()` called | unit |
| 7 | `test_not_found_error_is_permanent` | all | `NotFoundException` → immediate failure, no retry | unit |
| 8 | `test_validation_error_is_permanent` | all | `ValidationError` → immediate failure, no retry | unit |
| 9 | `test_already_exists_is_permanent` | `ingest_arxiv` | `AlreadyExistsException` → immediate failure | unit |
| 10 | `test_exhausted_retries_marks_failure` | all | After `MaxRetriesExceededError` → `job.status == failure` | unit |
| 11 | `test_exhausted_retries_publishes_failure` | all | Failure event published to WebSocket | unit |

### 6.2 Timeout Configuration

| # | Test | Task | Asserts | Marker |
|---|---|---|---|---|
| 1 | `test_embed_thesis_soft_time_limit` | `embed_thesis` | `soft_time_limit == 120` | unit |
| 2 | `test_embed_thesis_hard_time_limit` | `embed_thesis` | `time_limit == 180` | unit |
| 3 | `test_parse_transcript_soft_time_limit` | `parse_transcript` | `soft_time_limit == 300` | unit |
| 4 | `test_parse_transcript_hard_time_limit` | `parse_transcript` | `time_limit == 360` | unit |
| 5 | `test_chat_turn_soft_time_limit` | `process_chat_turn` | `soft_time_limit == 600` | unit |
| 6 | `test_chat_turn_hard_time_limit` | `process_chat_turn` | `time_limit == 660` | unit |
| 7 | `test_soft_timeout_marks_job_failure` | any | `SoftTimeLimitExceeded` → `job.status == failure`, `error` mentions "timeout" | unit |

---

## Phase 7 -- Regression Tests (Existing Code)

These tests verify the **current** behavior before any refactor. They form the safety net.
Write and pass them first.

### `tests/unit/test_compute_gpa.py`

Tests the pure function `_compute_gpa` from `app.students.service`.

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_gpa_three_courses` | Known courses → expected weighted average | unit |
| 2 | `test_gpa_weighted_by_credits` | 1-credit 1.0 + 5-credit 3.0 → (1*1.0 + 5*3.0) / 6 | unit |
| 3 | `test_gpa_empty_list` | `[]` → `None` | unit |
| 4 | `test_gpa_all_invalid_grades` | All grades "passed" → `None` | unit |
| 5 | `test_gpa_mixed_valid_and_invalid` | Some numeric, some "passed" → only numeric counted | unit |
| 6 | `test_gpa_german_comma_format` | `"1,3"` parsed as `1.3` | unit |
| 7 | `test_gpa_rounds_to_two_decimals` | Result has at most 2 decimal places | unit |

### `tests/unit/test_auth_service.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_register_creates_user` | `user_repo.create` called with email and hashed password | unit |
| 2 | `test_register_hashes_password` | Stored `password_hash` differs from plaintext input | unit |
| 3 | `test_register_duplicate_email_raises` | `AlreadyExistsException` | unit |
| 4 | `test_login_valid_credentials_returns_token` | `TokenResponse` with `access_token` string | unit |
| 5 | `test_login_unknown_email_raises` | `InvalidCredentialsException` | unit |
| 6 | `test_login_wrong_password_raises` | `InvalidCredentialsException` | unit |
| 7 | `test_get_user_by_id_returns_user` | `user_repo.get_by_id` called, returns user | unit |
| 8 | `test_get_user_by_id_not_found_raises` | `NotFoundException` | unit |

### `tests/unit/test_thesis_service.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_create_thesis_embeds_title_and_abstract` | `embed` called with `"{title}\n\n{abstract}"` | unit |
| 2 | `test_create_thesis_admin_source_is_professor` | Admin user → `source=ThesisSource.professor` | unit |
| 3 | `test_create_thesis_student_source_is_student` | Student user → `source=ThesisSource.student` | unit |
| 4 | `test_create_thesis_with_supervisor_validates_exists` | `supervisor_id=99` but user not found → `NotFoundException` | unit |
| 5 | `test_create_thesis_with_supervisor_validates_is_admin` | Supervisor is a student → `BadRequestException` | unit |
| 6 | `test_create_thesis_persists_and_commits` | `repo.create(...)` and `repo.commit()` both called | unit |
| 7 | `test_list_theses_passes_limit_and_offset` | `repo.list(limit=10, offset=5)` called with correct args | unit |
| 8 | `test_get_thesis_returns_thesis` | `repo.get_by_id(1)` returns thesis | unit |
| 9 | `test_get_thesis_not_found_raises` | `repo.get_by_id` returns `None` → `NotFoundException` | unit |

### `tests/unit/test_chair_service.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_create_chair_embeds_description` | `embed` called with `short_description` text | unit |
| 2 | `test_create_chair_stores_description_document` | `repo.add_document(kind=description, content=..., embedding=...)` called | unit |
| 3 | `test_create_chair_embed_failure_still_creates_chair` | `embed` raises → chair created, document stored with `embedding=None` | unit |
| 4 | `test_ingest_arxiv_validates_chair_exists` | `chair_id` not found → `NotFoundException` | unit |
| 5 | `test_ingest_arxiv_duplicate_raises` | Duplicate `arxiv_id` → `AlreadyExistsException` | unit |
| 6 | `test_ingest_arxiv_fetches_metadata` | `_fetch_arxiv_metadata(arxiv_id)` called (monkeypatched) | unit |
| 7 | `test_ingest_arxiv_embeds_abstract` | `embed` called with abstract text from fetched metadata | unit |
| 8 | `test_ingest_arxiv_stores_paper_document` | `repo.add_document(kind=paper, title=..., arxiv_id=..., embedding=...)` called | unit |
| 9 | `test_delete_chair_delegates` | `repo.delete(chair)` called | unit |
| 10 | `test_update_chair_patches_fields` | `repo.update(chair, **changed_fields)` called | unit |
| 11 | `test_get_chair_not_found_raises` | `NotFoundException` | unit |

### `tests/unit/test_student_service.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_get_profile_returns_student` | `repo.get_by_user_id(1)` called, returns student | unit |
| 2 | `test_get_profile_not_found_raises` | `repo.get_by_user_id` returns `None` → `NotFoundException` | unit |
| 3 | `test_upload_transcript_calls_extract_pdf` | `_extract_pdf_text` called with `pdf_bytes` (monkeypatched) | unit |
| 4 | `test_upload_transcript_calls_llm_chat_with_json_format` | `chat()` called with `format="json"` | unit |
| 5 | `test_upload_transcript_parses_llm_json_response` | Valid JSON → `TranscriptParseResult` with courses | unit |
| 6 | `test_upload_transcript_computes_gpa_from_courses` | GPA matches expected weighted average | unit |
| 7 | `test_upload_transcript_embeds_concatenated_courses` | `embed` called with `"Course A (5 ECTS); Course B (3 ECTS)"` pattern | unit |
| 8 | `test_upload_transcript_upserts_profile` | `repo.upsert(user_id, gpa=..., courses=..., embedding=...)` called | unit |
| 9 | `test_upload_transcript_empty_courses_gpa_none` | LLM returns 0 courses → GPA is `None`, profile still saved | unit |
| 10 | `test_upload_transcript_skips_invalid_course_rows` | 3 courses, 1 invalid → 2 persisted | unit |

### `tests/unit/test_chat_service.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_create_session_delegates` | `repo.create_session(user_id)` called | unit |
| 2 | `test_list_sessions_delegates` | `repo.list_sessions(user_id)` called | unit |
| 3 | `test_get_messages_validates_ownership` | Session belongs to other user → raises | unit |
| 4 | `test_send_message_persists_user_message` | `repo.create_message(role=user, content=...)` called | unit |
| 5 | `test_send_message_no_tool_calls` | LLM returns content → one assistant message persisted | unit |
| 6 | `test_send_message_with_tool_call` | LLM returns tool_call → tool executed → second LLM call → assistant message | unit |
| 7 | `test_send_message_max_iterations` | 6 rounds of tool calls → loop stops with limit message | unit |
| 8 | `test_build_student_context_with_courses` | Student has courses → context string includes names and GPA | unit |
| 9 | `test_build_student_context_no_student` | No student record → returns `None` | unit |

### `tests/e2e/test_health.py`

| # | Test | Asserts | Marker |
|---|---|---|---|
| 1 | `test_health_returns_ok` | `GET /api/health` → 200 `{"status": "ok"}` | e2e |

---

## Test Count Summary

| Phase | Unit | Integration | E2E | Total |
|---|---|---|---|---|
| 1. Celery + Redis | 12 | 0 | 0 | 12 |
| 2. Jobs | 19 | 8 | 6 | 33 |
| 3. WebSocket | 17 | 0 | 5 | 22 |
| 4. Ingestion tasks | 29 | 0 | 19 | 48 |
| 5. Chat worker | 23 | 0 | 10 | 33 |
| 6. Error/retry | 18 | 0 | 0 | 18 |
| 7. Regression | 55 | 0 | 1 | 56 |
| **Total** | **173** | **8** | **41** | **222** |

---

## Execution Order

Write tests in this order. Each group must pass before moving to the next.

### Step 1: Test infrastructure + Regression (Phase 0 + 7)

1. Create directory structure and `conftest.py` files with fixtures.
2. Write and pass `test_compute_gpa.py` (pure function, no mocks).
3. Write and pass `test_auth_service.py`.
4. Write and pass `test_thesis_service.py`.
5. Write and pass `test_chair_service.py`.
6. Write and pass `test_student_service.py`.
7. Write and pass `test_chat_service.py`.
8. Write and pass `test_health.py`.

These all test the **existing** codebase with no changes. They are the safety net.

### Step 2: Phase 1 (Celery infrastructure)

1. Write `test_celery_config.py` and `test_run_async.py` — tests will fail.
2. Implement `app/worker/` module — tests pass.

### Step 3: Phase 2 (Jobs)

1. Write `test_job_schemas.py`, `test_job_service.py`, `test_job_repository.py`,
   `test_job_endpoints.py` — tests will fail.
2. Implement jobs model, migration, domain module — tests pass.

### Step 4: Phase 3 (WebSocket)

1. Write `test_connection_manager.py`, `test_listener.py`, `test_publisher.py`,
   `test_ws_endpoints.py` — tests will fail.
2. Implement WebSocket module — tests pass.

### Step 5: Phase 4 (Ingestion tasks)

1. Write `test_thesis_tasks.py` and updated `test_thesis_endpoints.py` — tests will fail.
2. Implement thesis task + controller change — tests pass.
3. Repeat for chairs (ArXiv + description embedding).
4. Repeat for students (transcript).

### Step 6: Phase 5 (Chat worker)

1. Write `test_chat_tasks.py` and updated `test_chat_endpoints.py` — tests will fail.
2. Implement chat task + controller change — tests pass.

### Step 7: Phase 6 (Error hardening)

1. Write retry/timeout tests — some may already pass from Phase 4/5 implementation.
2. Configure retry policies and timeouts — all tests pass.

---

## Running Tests

```bash
# From backend/ directory

# All tests
uv run pytest

# Unit tests only (fast, no DB required)
uv run pytest -m unit

# Integration tests (requires TEST_DATABASE_URL env var)
TEST_DATABASE_URL="postgresql+asyncpg://thesis:thesis@localhost:5433/thesis_test" \
  uv run pytest -m integration

# E2E tests
uv run pytest -m e2e

# With coverage report
uv run pytest --cov=app --cov-report=term-missing

# Single file
uv run pytest tests/unit/test_thesis_service.py -v

# Single test
uv run pytest tests/unit/test_thesis_service.py::test_create_thesis_embeds_title_and_abstract -v
```

---

## Mocking Patterns

### Mock `LLMPort`

```python
from unittest.mock import AsyncMock

mock_llm = AsyncMock()
mock_llm.chat.return_value = {
    "message": {"role": "assistant", "content": "Hello!", "tool_calls": []}
}
mock_llm.embed.return_value = [0.1] * 2560
mock_llm.aclose.return_value = None
```

### Mock Repository

```python
mock_repo = AsyncMock()
mock_repo.get_by_id.return_value = fake_thesis
mock_repo.create.return_value = fake_thesis
mock_repo.commit.return_value = None
```

### Monkeypatch Module-Level Functions

```python
async def test_ingest_arxiv(monkeypatch):
    fake_metadata = {"title": "Paper", "abstract": "Abstract", "year": 2024}
    monkeypatch.setattr(
        "app.chairs.service._fetch_arxiv_metadata",
        AsyncMock(return_value=fake_metadata),
    )
```

### Override FastAPI Dependencies (E2E)

```python
from app.auth.deps import get_current_user, get_session

app.dependency_overrides[get_current_user] = lambda: fake_user
app.dependency_overrides[get_session] = override_get_session
```

### Mock Celery Task Dispatch

```python
from unittest.mock import patch

with patch("app.theses.tasks.embed_thesis.delay") as mock_delay:
    mock_delay.return_value = MockAsyncResult(id="task-123")
    response = await client.post("/api/theses", json=data)
    mock_delay.assert_called_once_with(thesis_id)
```
