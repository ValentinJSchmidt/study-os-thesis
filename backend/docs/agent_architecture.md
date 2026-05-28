# Agent Architecture & RAG Pipeline

This document gives an overview of how the AI agent and retrieval-augmented generation (RAG) pipeline work together in the Study-OS thesis advisor backend.

---

## 1. High-Level System Overview

```mermaid
flowchart TD
    FE["Frontend (React/Vite)"]
    API["FastAPI Application"]
    AGENT["ChatService\n(ReAct Agent Loop)"]
    LLM["LLM Layer\n(OllamaClient / LiteLLMAdapter)"]
    DB[("PostgreSQL 16\n+ pgvector")]

    FE -- "HTTP / JWT" --> API
    API -- "POST /api/chat/sessions/{id}/messages" --> AGENT
    AGENT -- "chat() / embed()" --> LLM
    AGENT -- "read/write messages,\nproposals, profiles" --> DB
    LLM -- "qwen3-embedding:4b\ngemma4:26b (default)" --> OLLAMA["Ollama / Azure / DeepSeek"]
```

---

## 2. Agent Loop (ReAct Pattern)

The agent follows a **Reason → Act → Observe** cycle capped at **6 iterations** per user message.

```mermaid
flowchart TD
    START(["User sends message\nPOST /messages"])
    CTX["Load student context\n(GPA, program, courses)"]
    HIST["Load chat history\n(last 20 messages)"]
    BUILD["Build message array\n[system+context, history, user_msg]"]
    LLM_CALL["LLM.chat(messages, tools=TOOLS_SPEC)"]
    HAS_TOOLS{Tool calls\nin response?}
    EXEC["Execute tool calls\n(search_chairs / search_theses / generate_proposal)"]
    PERSIST_TOOL["Persist: assistant msg\n+ tool result msgs to DB"]
    APPEND["Append results to\nmessage array"]
    MAX{Max iterations\nreached? (6)}
    PERSIST_FINAL["Persist final\nassistant text to DB"]
    COMMIT["Commit transaction\n(all turn messages atomically)"]
    RETURN(["Return all new messages\nto frontend"])

    START --> CTX --> HIST --> BUILD --> LLM_CALL
    LLM_CALL --> HAS_TOOLS
    HAS_TOOLS -- "Yes" --> EXEC --> PERSIST_TOOL --> APPEND --> MAX
    MAX -- "No" --> LLM_CALL
    MAX -- "Yes (force stop)" --> PERSIST_FINAL
    HAS_TOOLS -- "No (plain text)" --> PERSIST_FINAL
    PERSIST_FINAL --> COMMIT --> RETURN
```

---

## 3. Agent Tools

The agent has three tools available, declared as `TOOLS_SPEC` in `app/chat/service.py`.

```mermaid
flowchart LR
    AGENT["ChatService\n_execute_tool_call()"]

    AGENT -- "search_chairs\n(query, k)" --> T1["_tool_search_chairs\n→ embed query\n→ ChairRepository.search_by_embedding\n→ vector cosine scan"]

    AGENT -- "search_theses\n(query, k, chair_id?)" --> T2["_tool_search_theses\n→ search_theses_with_client()\n→ hybrid BM25 + vector + RRF"]

    AGENT -- "generate_proposal\n(chair_id, direction, count)" --> T3["_tool_generate_proposal\n→ build prompt\n→ LLM.chat() for JSON\n→ embed each proposal\n→ save to theses table"]
```

---

## 4. RAG Pipeline — Document Ingestion

There are three separate ingestion paths feeding the knowledge base.

### 4.1 Chair Knowledge Base

```mermaid
flowchart TD
    subgraph "Path A: Chair Description"
        A1["POST /api/chairs\n(admin)"] --> A2["ChairService.create_chair"]
        A2 --> A3["embed_client.embed(short_description)"]
        A3 --> A4["INSERT chair_documents\nkind=description\nembedding=vector(2560)"]
    end

    subgraph "Path B: ArXiv Paper"
        B1["POST /api/chairs/{id}/documents/arxiv\n(admin)"] --> B2["ChairService.ingest_arxiv_paper"]
        B2 --> B3["HTTP GET arxiv.org/api/query\n→ parse Atom XML\n→ title + abstract"]
        B3 --> B4["embed_client.embed(abstract)"]
        B4 --> B5["INSERT chair_documents\nkind=paper\nembedding=vector(2560)"]
    end

    A4 --> VDB[("chair_documents\nVector(2560)")]
    B5 --> VDB
```

### 4.2 Student Profile Embedding

```mermaid
flowchart TD
    U1["POST /api/students/me/transcript\n(multipart PDF)"] --> U2["StudentService.upload_transcript"]

    U2 --> S1["Step 1: PDF Extraction\npdfplumber → tables as Markdown\n+ plain text"]
    S1 --> S2["Step 2: LLM Structured Extraction\nLLM.chat(format=json)\n→ TranscriptParseResult\n{gpa, courses[]}"]
    S2 --> S3["Step 3: GPA Computation\ncredit-weighted avg\n(German 1.0–5.0 scale)"]
    S3 --> S4["Step 4: Profile Embedding\nembed_client.embed\n('CourseA (7.5 ECTS); ...')\n→ vector(2560)"]
    S4 --> S5["Step 5: DB Upsert\nStudentRepository.upsert\nstudents + student_courses"]

    S5 --> DB1[("students\nprofile_embedding Vector(2560)\n\nstudent_courses")]
```

### 4.3 Thesis Embedding (professor-created & AI-generated)

```mermaid
flowchart TD
    P1["POST /api/theses\n(professor/admin)"] --> TE["ThesisService.create_thesis\nembed(title + abstract)\n→ INSERT theses"]

    P2["Agent: generate_proposal tool"] --> GE["ChatService._tool_generate_proposal\nLLM generates JSON proposals\nembed(title + abstract)\n→ INSERT theses\n(source=student)"]

    TE --> TDB[("theses\nembedding Vector(2560)\nsearch_vec TSVECTOR GENERATED")]
    GE --> TDB
```

---

## 5. RAG Pipeline — Retrieval

### 5.1 Hybrid Thesis Search (BM25 + Vector + RRF)

`app/tools/search_theses.py` — called by the `search_theses` agent tool.

```mermaid
flowchart TD
    Q["query (str)"]

    Q --> VEC["Vector Leg\nembed_client.embed(query)\n→ vector(2560)\n\nSELECT ... embedding <=> query_vec\nORDER BY cosine distance ASC\nLIMIT fetch"]

    Q --> BM25["BM25 Leg\nSELECT ... ts_rank_cd(search_vec,\nplainto_tsquery('english', q))\nWHERE search_vec @@ plainto_tsquery\nGIN index"]

    VEC --> GATHER["asyncio.gather\n(parallel execution)"]
    BM25 --> GATHER

    GATHER --> RRF["RRF Fusion\n∑ 1 / (rank + 1 + 60)\nper doc from both lists\ndedup by thesis ID\nsort by combined score"]

    RRF --> TOPK["Top-k ThesisHit list\n{id, title, abstract, score}\nreturned as JSON to agent"]

    style VEC fill:#dbeafe
    style BM25 fill:#dcfce7
    style RRF fill:#fef9c3
```

**Fallback behaviour:** If Ollama is offline → BM25 only. If no BM25 hits → vector only. Both empty → `[]`.

### 5.2 Chair Semantic Search

`app/chairs/repository.py` — called by the `search_chairs` agent tool.

```mermaid
flowchart TD
    Q2["query (str)"]
    Q2 --> E["embed_client.embed(query)\n→ vector(2560)"]
    E --> SQL["SELECT chair_documents\nORDER BY embedding <=> query_vec ASC\n(exact sequential scan, 2560d > HNSW limit)\nLIMIT k"]
    SQL --> DEDUP["Deduplicate by chair_id\n(already_seen flag)"]
    DEDUP --> OUT["list of chairs\n{chair_id, chair_name, professor,\nsnippet, score, already_seen}"]
```

---

## 6. LLM Provider Layer

```mermaid
flowchart LR
    SVC["Services\n(ChatService,\nStudentService,\nChairService,\nThesisService)"]

    SVC -- "LLMPort.chat()\nLLMPort.embed()" --> PORT["LLMPort Protocol\n(app/llm/port.py)"]

    PORT --> FAC["LLM Factory\nbuild_chat_client()\nbuild_embed_client()"]

    FAC -- "LLM_CHAT/EMBED_PROVIDER=ollama" --> OL["OllamaClient\nhttpx async\nPOST /api/chat\nPOST /api/embed"]
    FAC -- "LLM_CHAT_PROVIDER=azure\nor deepseek" --> LL["LiteLLMAdapter\nnormalises responses\nto Ollama dict shape"]

    OL --> OLLAMA["Ollama\ngemma4:26b (chat)\nqwen3-embedding:4b (embed)"]
    LL --> AZURE["Azure OpenAI\nor DeepSeek"]
```

Two independent client singletons are created at startup and stored in `app.state`:
- `llm_chat_client` — used for the agent loop and proposal generation
- `llm_embed_client` — used for all embedding calls

---

## 7. Data Models & Storage

```mermaid
erDiagram
    users {
        int id PK
        string email
        string password_hash
        string role
    }
    chat_sessions {
        int id PK
        int user_id FK
        datetime created_at
    }
    chat_messages {
        int id PK
        int session_id FK
        string role
        text content
        jsonb tool_calls
        string tool_call_id
        string tool_name
        datetime created_at
    }
    students {
        int user_id PK
        string program
        int semester
        numeric gpa
        vector profile_embedding
        datetime updated_at
    }
    student_courses {
        int id PK
        int student_id FK
        string course_name
        numeric credits
        string grade
        string semester_taken
    }
    chairs {
        int id PK
        string name
        string short_description
        string professor_name
        int professor_user_id FK
        string website_url
    }
    chair_documents {
        int id PK
        int chair_id FK
        string kind
        string title
        text content
        string arxiv_id
        int published_year
        vector embedding
        datetime created_at
    }
    theses {
        int id PK
        string title
        text abstract
        int chair_id FK
        int supervisor_id FK
        int submitter_id FK
        string source
        string difficulty
        jsonb skills_required
        int generated_for_user_id FK
        int chat_session_id FK
        vector embedding
        tsvector search_vec
        datetime created_at
    }

    users ||--o{ chat_sessions : "has"
    chat_sessions ||--o{ chat_messages : "contains"
    users ||--o| students : "is"
    students ||--o{ student_courses : "has"
    users ||--o{ chairs : "leads"
    chairs ||--o{ chair_documents : "has"
    chairs ||--o{ theses : "offers"
    users ||--o{ theses : "submitted"
    users ||--o{ theses : "generated for"
    chat_sessions ||--o{ theses : "triggered"
```

---

## 8. Request Flow: Full Chat Turn

End-to-end flow from user message to response, showing all layers.

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI
    participant CS as ChatService
    participant LLM as LLM (chat)
    participant EMB as LLM (embed)
    participant DB as PostgreSQL

    FE->>API: POST /api/chat/sessions/{id}/messages\n{content: "Help me find a thesis"}
    API->>CS: send_message(session_id, user_id, content)

    CS->>DB: load last 20 chat_messages
    CS->>DB: load student profile (GPA, courses)
    note over CS: Build [system+context, history, user_msg]

    loop ReAct loop (max 6 iterations)
        CS->>LLM: chat(messages, tools=TOOLS_SPEC)
        LLM-->>CS: {tool_calls: [{name, arguments}]}
        CS->>DB: flush assistant msg (with tool_calls)

        alt search_chairs
            CS->>EMB: embed(query)
            EMB-->>CS: vector[2560]
            CS->>DB: SELECT chair_documents ORDER BY cosine ASC
            DB-->>CS: chair results
        else search_theses
            CS->>EMB: embed(query)
            EMB-->>CS: vector[2560]
            CS->>DB: vector search + BM25 search (parallel)
            DB-->>CS: thesis results
            note over CS: RRF fusion
        else generate_proposal
            CS->>LLM: chat(proposal prompt, format=json)
            LLM-->>CS: [{title, abstract, ...}]
            CS->>EMB: embed(title + abstract)
            EMB-->>CS: vector[2560]
            CS->>DB: INSERT theses (source=student)
        end

        CS->>DB: flush tool result msg
    end

    CS->>LLM: chat(messages) — final reasoning
    LLM-->>CS: {content: "Here are my recommendations..."}
    CS->>DB: flush final assistant msg
    CS->>DB: COMMIT (all turn messages atomic)
    CS-->>API: [user_msg, tool_results..., assistant_msg]
    API-->>FE: SendMessageResponse
```

---

## 9. Key Design Decisions

| Decision | Details |
|---|---|
| **ReAct-style single agent** | One `ChatService` agent, no multi-agent orchestration. The LLM decides which tools to call; tool results are fed back into context. |
| **Port-adapter for LLM** | `LLMPort` Protocol decouples all business logic from the LLM provider. Swap Ollama → Azure with an env var. |
| **Dual LLM clients** | Separate `chat_client` and `embed_client` singletons allow mixing providers (e.g., DeepSeek for chat, Ollama for embed since DeepSeek has no embed API). |
| **Hybrid search (BM25 + Vector + RRF)** | Thesis search combines lexical (PostgreSQL tsvector/GIN) and semantic (pgvector cosine) signals, fused with Reciprocal Rank Fusion. Runs both legs in parallel. |
| **Sequential scan for vectors** | Embedding dimension is 2560 (qwen3-embedding:4b), which exceeds pgvector's HNSW/IVFFlat limit of 2000. All vector searches use exact sequential scan — acceptable at research-project scale. |
| **Atomic message commits** | All messages in a single agent turn are flushed during the loop but committed in one transaction at the end, preventing partial turns from appearing in history on failure. |
| **Student context injection** | Student GPA and course list are injected into the system prompt every turn — the agent does not need a "get profile" tool call. |
| **Generated proposal traceability** | Each AI-generated thesis in `theses` carries both `generated_for_user_id` and `chat_session_id`. |
