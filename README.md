# study-os-thesis

A web app that recommends theses to students through a Q&A chat with a local LLM.
Professors and students submit thesis topics; a tool-using LLM agent searches
them by semantic similarity (pgvector) and discusses options with the student.

## Stack

- **Backend**: FastAPI + async SQLAlchemy + Alembic, dependency-managed by `uv`
- **DB**: PostgreSQL 16 + pgvector (run via Docker, on host port **5433**)
- **LLM**: Local Ollama (`llama3.1:8b` for chat, `nomic-embed-text` for embeddings)
- **Frontend**: React + TypeScript via Vite

Everything runs locally — no cloud accounts or API keys required.

## Prerequisites

Install these once:

1. **Docker Desktop** with WSL2 integration enabled
   (Settings → Resources → WSL Integration → toggle your distro, then Apply & Restart).
   On Linux without Docker Desktop, the regular `docker` daemon works too.
2. **uv** (Python package manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Restart your shell or `source ~/.bashrc` afterwards so `uv` is on PATH.
3. **Ollama**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text
   ```
   The two models add up to ~5 GB. The first chat response in a fresh process
   takes 30–90 seconds on CPU while the model loads into RAM; subsequent
   responses are much faster.
4. **Node.js** ≥ 20 (for the frontend).

## First-time setup

```bash
git clone <repo-url> study-os-thesis
cd study-os-thesis

# 1. Database (Postgres + pgvector, listens on host port 5433)
docker compose up -d

# 2. Backend
cd backend
cp .env.example .env
# Generate a real JWT secret:
python -c "import secrets; print(f'JWT_SECRET={secrets.token_urlsafe(32)}')" \
  | tee -a .env
# (then remove the placeholder JWT_SECRET line from .env, or edit by hand)
uv sync
uv run alembic upgrade head

# 3. Run the API
uv run uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Test users for trying it out

Once the API is running, the easiest way to populate some realistic data is to
register two accounts and have the professor submit a few thesis topics. The
following accounts and prompts are what we use locally — feel free to copy them.

| Email | Password | Role | What for |
|---|---|---|---|
| `prof@example.com` | `password123` | professor | Submits thesis topics |
| `stu@example.com`  | `password123` | student   | Chats with the LLM to get recommendations |


**Step 1 — register them.** Either through the React UI at
`http://localhost:5173/register`, or via Swagger at `http://localhost:8000/docs`
on `POST /api/auth/register`. Pick the role from the dropdown.

> ⚠️ Email validation requires a real-looking domain. `prof@x` will be rejected;
> `prof@example.com` works.

**Step 2 — seed a few theses as the professor.** Log in as `prof@example.com`,
go to **Submit thesis**, and paste any of these (each takes ~1 s to embed):

<details>
<summary>Sample thesis 1 — Graph Neural Networks</summary>

- **Title**: Graph Neural Networks for Drug Discovery
- **Abstract**: This thesis explores applying GNN architectures (GCN, GAT, MPNN)
  to molecular property prediction and de novo drug design. We benchmark against
  transformer baselines on QM9 and MoleculeNet.
</details>

<details>
<summary>Sample thesis 2 — Differential Privacy</summary>

- **Title**: Differential Privacy in Federated Learning
- **Abstract**: A study of DP-SGD applied to cross-device federated learning
  settings. We measure privacy/utility tradeoffs on CIFAR and Shakespeare
  benchmarks with varying epsilon.
</details>

<details>
<summary>Sample thesis 3 — Spaced Repetition</summary>

- **Title**: Adaptive Spaced Repetition for University Learners
- **Abstract**: This thesis designs a spaced-repetition scheduler driven by a
  Bayesian item-response model, evaluating retention on a cohort of 200
  students over one semester.
</details>

**Step 3 — chat as the student.** Log out, log in as `stu@example.com`, click
**Chat → + New session**, and try messages like:

- "I'm interested in deep learning on graphs and chemistry applications."
- "I want to do something with privacy in machine learning."
- "What topics combine cognitive science and AI?"

The assistant should call the `search_theses` tool (visible as a collapsible
panel in the UI) and recommend matching theses by their IDs.

## Running it day-to-day

After the first-time setup, the loop is:

```bash
docker compose up -d                                  # DB
cd backend && uv run uvicorn app.main:app --reload    # terminal 1
cd frontend && npm run dev                            # terminal 2
```

To shut down: kill the two dev servers, then `docker compose down`. Add `-v`
(`docker compose down -v`) only if you want to wipe the database volume.

## Project layout

```
backend/
  app/
    api/             FastAPI routers: auth, theses, chat, admin
    auth/            Password hashing + JWT
    llm/             Ollama client, embeddings, agent (tool-calling loop)
    models/          SQLAlchemy models
    schemas/         Pydantic in/out models
    tools/           search_theses (pgvector cosine search)
  alembic/           DB migrations
  scripts/           check_ollama, check_search
frontend/
  src/
    api/             fetch wrapper + JWT handling
    auth/            React auth context
    pages/           Login, Register, SubmitThesis, Chat, Admin
docker-compose.yml   Postgres + pgvector on host port 5433
```

## Troubleshooting

A few rough edges we ran into on first setup — keeping notes here so the next
collaborator can fix them in seconds.

### Docker says "command not found" inside WSL

In Docker Desktop → Settings → Resources → **WSL Integration** → enable
integration with your default distro → Apply & Restart. Then in PowerShell
verify your distro is on WSL 2 with `wsl -l -v`.

### `docker compose pull` fails with `docker-credential-desktop.exe: exec format error`

Docker Desktop's credential helper is a Windows binary that can't run inside
WSL. We only pull public images, so just clear the credsStore:

```bash
echo '{}' > ~/.docker/config.json
```

### `password authentication failed for user "thesis"` from the host

You already have a Postgres on port 5432. Our compose file maps the container
to **5433** to avoid the clash — make sure `DATABASE_URL` in `backend/.env`
ends with `:5433/thesis`, not `:5432/thesis`.

If you previously brought the container up on 5432 with the wrong creds, wipe
the volume and recreate:

```bash
docker compose down -v
docker compose up -d
```

### `ValueError: password cannot be longer than 72 bytes` during register

That's passlib 1.7 against bcrypt ≥ 4.1. `pyproject.toml` pins `bcrypt<4.1` —
make sure you ran `uv sync` and not just `pip install`.

### First chat message times out

Llama 3.1 8B takes 30–90 s to load on CPU. We bumped the httpx timeout to
600 s — first message will feel slow, the rest snappy. To pre-warm:

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"llama3.1:8b","prompt":"hi","stream":false}' >/dev/null
```

### `ModuleNotFoundError: No module named 'app'` running a script

Run scripts from the `backend/` directory: `uv run python scripts/<name>.py`.
The scripts add the parent dir to `sys.path` automatically, but `cwd` must be
`backend/`.

## Out of scope (not yet implemented)

- OpenAlex / external scraping
- File upload / PDF parsing for theses
- Password reset, email verification, refresh tokens
- Automated tests (pytest scaffold is installed but no tests written yet)
