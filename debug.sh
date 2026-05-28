#!/usr/bin/env bash
set -uo pipefail
# Enable job control so each background job gets its own process group.
# This lets us kill the whole group (uvicorn + workers, vite + node, etc.)
# with a single signal.
set -m

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
ENV_FILE="$BACKEND_DIR/.env"
ENV_EXAMPLE="$BACKEND_DIR/.env.example"

# PIDs of background processes (for cleanup)
BACKEND_PID=""
FRONTEND_PID=""

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

info()  { printf "\033[1;34m[info]\033[0m  %s\n" "$*"; }
warn()  { printf "\033[1;33m[warn]\033[0m  %s\n" "$*"; }
error() { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; }
die()   { error "$*"; exit 1; }

check_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "'$1' is not installed. Please install it first."
}

kill_pid() {
  local pid="$1"
  [[ -z "$pid" ]] && return 0

  # First try SIGTERM on the process group
  if kill -0 "$pid" 2>/dev/null; then
    kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  fi

  # Wait briefly for graceful shutdown
  local i=0
  while [[ $i -lt 10 ]] && kill -0 "$pid" 2>/dev/null; do
    sleep 0.2
    i=$((i + 1))
  done

  # Force-kill if still alive
  if kill -0 "$pid" 2>/dev/null; then
    kill -9 -- -"$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
  fi
}

cleanup() {
  # Prevent the trap from running multiple times
  trap - SIGINT SIGTERM EXIT

  info "Shutting down app processes..."
  kill_pid "$BACKEND_PID"
  kill_pid "$FRONTEND_PID"
  wait 2>/dev/null || true

  info "App stopped. Docker containers are still running."
  info "Run '$0 down' to stop the database container."
}

# Check if the DB container is already healthy (instant check, no polling).
db_is_healthy() {
  docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps "db" 2>/dev/null \
    | grep -q "(healthy)"
}

wait_for_healthy() {
  local service="$1"
  local timeout="${2:-60}"
  local elapsed=0

  info "Waiting for $service to be healthy (timeout: ${timeout}s)..."
  while [[ $elapsed -lt $timeout ]]; do
    if docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps "$service" 2>/dev/null \
        | grep -q "(healthy)"; then
      info "$service is healthy."
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  die "$service did not become healthy within ${timeout}s."
}

# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

# Shared setup: .env, deps, migrations — used by both cmd_start and cmd_up.
setup() {
  # -- .env ----------------------------------------------------------------- #
  if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$ENV_EXAMPLE" ]]; then
      cp "$ENV_EXAMPLE" "$ENV_FILE"
      warn ".env not found — created from .env.example. Review $ENV_FILE if needed."
    else
      die "No .env or .env.example found in $BACKEND_DIR"
    fi
  fi

  # Export variables for subprocesses
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a

  # -- Backend dependencies ------------------------------------------------- #
  local uv_marker="$BACKEND_DIR/.venv/.uv-synced"
  if [[ ! -d "$BACKEND_DIR/.venv" ]] \
     || [[ ! -f "$uv_marker" ]] \
     || [[ "$BACKEND_DIR/uv.lock" -nt "$uv_marker" ]] \
     || [[ "$BACKEND_DIR/pyproject.toml" -nt "$uv_marker" ]]; then
    info "Installing backend dependencies..."
    (cd "$BACKEND_DIR" && uv sync)
    # macOS Gatekeeper performs slow trustd checks on unsigned .so files.
    # Ad-hoc signing (no Apple Developer account required) makes dlopen fast.
    # if [[ "$(uname)" == "Darwin" ]]; then
    #   info "Ad-hoc signing native extensions (macOS Gatekeeper fix)..."
    #   find "$BACKEND_DIR/.venv" -name "*.so" -print0 \
    #     | xargs -0 -P "$(sysctl -n hw.logicalcpu)" codesign --sign - --force 2>/dev/null || true
    # fi
    touch "$uv_marker"
  else
    info "Backend dependencies up to date — skipping."
  fi

  # -- Frontend dependencies ------------------------------------------------ #
  local npm_marker="$FRONTEND_DIR/node_modules/.npm-installed"
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]] \
     || [[ ! -f "$npm_marker" ]] \
     || [[ "$FRONTEND_DIR/package-lock.json" -nt "$npm_marker" ]] \
     || [[ "$FRONTEND_DIR/package.json" -nt "$npm_marker" ]]; then
    info "Installing frontend dependencies..."
    (cd "$FRONTEND_DIR" && npm install)
    touch "$npm_marker"
  else
    info "Frontend dependencies up to date — skipping."
  fi

  # -- Database migrations -------------------------------------------------- #
  local alembic_marker="$BACKEND_DIR/.venv/.alembic-ran"
  local migrations_dir="$BACKEND_DIR/alembic/versions"
  local need_migrate=false

  if [[ ! -f "$alembic_marker" ]]; then
    need_migrate=true
  else
    while IFS= read -r -d '' mfile; do
      if [[ "$mfile" -nt "$alembic_marker" ]]; then
        need_migrate=true
        break
      fi
    done < <(find "$migrations_dir" -name '*.py' -print0 2>/dev/null)
  fi

  if [[ "$need_migrate" == true ]]; then
    info "Running database migrations..."
    (cd "$BACKEND_DIR" && uv run alembic upgrade head)
    touch "$alembic_marker"
  else
    info "Migrations up to date — skipping."
  fi

}

# Launch backend + frontend and wait.
run_app() {
  trap cleanup SIGINT SIGTERM EXIT

  mkdir -p "$BACKEND_DIR/logs"

  info "Starting backend (uvicorn) on port 8000..."
  # LITELLM_LOCAL_MODEL_COST_MAP suppresses LiteLLM's network call to fetch pricing data.
  # LITELLM_DONT_SHOW_FEEDBACK_BOX suppresses the interactive prompt.
  (cd "$BACKEND_DIR" && exec env \
    LITELLM_LOCAL_MODEL_COST_MAP=1 \
    LITELLM_DONT_SHOW_FEEDBACK_BOX=1 \
    uv run uvicorn app.main:app \
      --reload \
      --reload-include "app/**/*.py" \
      --reload-dir app \
      --port 8000 \
      --log-config log_config.json) &
  BACKEND_PID=$!

  info "Starting frontend (vite) on port 5173..."
  (cd "$FRONTEND_DIR" && exec npm run dev) &
  FRONTEND_PID=$!

  echo ""
  info "========================================="
  info "  Frontend : http://localhost:5173"
  info "  Backend  : http://localhost:8000"
  info "  API docs : http://localhost:8000/docs"
  info "========================================="
  info "Press Ctrl+C to stop the app."
  echo ""

  wait || true
}

# ./debug.sh  (no args) — start the app, assume containers are already running.
cmd_start() {
  check_cmd uv
  check_cmd npm

  if ! db_is_healthy; then
    die "DB container is not running/healthy. Run '$0 up' first to start containers."
  fi

  setup
  run_app
}

# ./debug.sh up — start containers, then the app.
cmd_up() {
  check_cmd docker
  check_cmd uv
  check_cmd npm

  info "Starting Docker containers..."
  docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d

  if db_is_healthy; then
    info "DB is already healthy."
  else
    wait_for_healthy "db" 60
  fi

  setup
  run_app
}

# ./debug.sh down — stop containers only.
cmd_down() {
  info "Stopping Docker containers..."
  docker compose -f "$SCRIPT_DIR/docker-compose.yml" down
  info "Containers stopped. (Volumes preserved.)"
}

# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #

usage() {
  echo "Usage: $0 [up|down]"
  echo ""
  echo "  (none)  Start the app (containers must already be running)"
  echo "  up      Start containers, then start the app"
  echo "  down    Stop Docker containers (volumes preserved)"
  exit 1
}

case "${1:-}" in
  "")   cmd_start ;;
  up)   cmd_up    ;;
  down) cmd_down  ;;
  *)    usage     ;;
esac
