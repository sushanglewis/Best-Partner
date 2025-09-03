#!/usr/bin/env bash
# One-click starter for Postgres, Backend, Agent (Docker), Frontend
# Follows SSOT ports from .env; prohibits port drift and duplicate instances.
set -euo pipefail

# --- Helpers ---
log() { printf "\033[1;32m[OK]\033[0m %s\n" "$*"; }
info() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[ERR]\033[0m %s\n" "$*"; }
require_cmd() { command -v "$1" >/dev/null 2>&1 || { err "Missing command: $1"; exit 1; }; }
port_in_use() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
port_owner_cmd() { lsof -nP -iTCP:"$1" -sTCP:LISTEN -Fp | sed -n 's/^p//p' | xargs -I{} ps -o comm= -p {} 2>/dev/null | head -n1; }

# --- Project root ---
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# --- Load .env as SSOT ---
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set -a
  info "Loaded .env"
else
  warn ".env not found at project root; falling back to defaults."
fi

# --- SSOT Ports with defaults ---
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
BACKEND_PORT="${VITE_BACKEND_PORT:-${BACKEND_PORT:-8080}}"
AGENT_PORT="${AGENT_PORT:-2024}"
FRONTEND_PORT="${VITE_PORT:-${FRONTEND_PORT:-5174}}"
REDIS_PORT="${REDIS_PORT:-6379}"

# --- Postgres credentials (must be provided in .env ideally) ---
POSTGRES_USER="${POSTGRES_USER:-bestpartners}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-bestpartners}"
POSTGRES_DB="${POSTGRES_DB:-bestpartners}"

# --- Docker resources ---
POSTGRES_IMAGE="postgres:15-alpine"
AGENT_IMAGE="best-partners-agent:latest"
POSTGRES_CONTAINER="bp-postgres"
AGENT_CONTAINER="bp-agent"
REDIS_IMAGE="redis:7-alpine"
REDIS_CONTAINER="bp-redis"
DOCKER_NETWORK="bp-net"

# Track how Redis is provided: container|external
REDIS_MODE="container"

# --- Pre-flight checks ---
require_cmd docker
require_cmd lsof
require_cmd curl

# Frontend uses Node.js
if ! command -v node >/dev/null 2>&1; then
  warn "node is not installed; frontend may fail to start."
fi

# --- Functions ---
ensure_network_exists() {
  if ! docker network inspect "$DOCKER_NETWORK" >/dev/null 2>&1; then
    info "Creating docker network $DOCKER_NETWORK..."
    docker network create "$DOCKER_NETWORK" >/dev/null
  fi
}

start_postgres() {
  info "Starting Postgres ($POSTGRES_IMAGE) on port $POSTGRES_PORT..."
  if docker ps -a --format '{{.Names}} {{.Status}}' | grep -E "^${POSTGRES_CONTAINER} " >/dev/null 2>&1; then
    local status
    status="$(docker ps -a --format '{{.Names}} {{.Status}}' | awk "/^${POSTGRES_CONTAINER} /{print substr($0, index($0,$2))}")"
    if echo "$status" | grep -qi "Up"; then
      info "Container ${POSTGRES_CONTAINER} is already running."
    else
      info "Starting existing container ${POSTGRES_CONTAINER}..."
      docker start "$POSTGRES_CONTAINER" >/dev/null
    fi
  else
    if port_in_use "$POSTGRES_PORT"; then
      local owner; owner="$(port_owner_cmd "$POSTGRES_PORT" || true)"
      info "Detected existing Postgres (or another service) on port $POSTGRES_PORT (owner: ${owner:-unknown}). Will reuse external instance and skip creating ${POSTGRES_CONTAINER}."
    else
      info "Creating container ${POSTGRES_CONTAINER}..."
      ensure_network_exists
      docker run -d \
        --name "$POSTGRES_CONTAINER" \
        --restart unless-stopped \
        --network "$DOCKER_NETWORK" \
        -e POSTGRES_USER="$POSTGRES_USER" \
        -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        -e POSTGRES_DB="$POSTGRES_DB" \
        -p "$POSTGRES_PORT:5432" \
        -v bp_pgdata:/var/lib/postgresql/data \
        "$POSTGRES_IMAGE" >/dev/null
    fi
  fi

  # Wait for Postgres readiness (best effort)
  info "Waiting for Postgres to become ready..."
  local tries=0
  if docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    until docker exec "$POSTGRES_CONTAINER" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h 127.0.0.1 >/dev/null 2>&1; do
      tries=$((tries+1))
      if [ "$tries" -gt 60 ]; then
        err "Postgres did not become ready in time."
        exit 1
      fi
      sleep 1
    done
  else
    # External Postgres on host: try TCP check if nc available, else wait a bit
    if command -v nc >/dev/null 2>&1; then
      until nc -z 127.0.0.1 "$POSTGRES_PORT" >/dev/null 2>&1; do
        tries=$((tries+1))
        if [ "$tries" -gt 60 ]; then
          err "External Postgres on port $POSTGRES_PORT is not reachable."
          exit 1
        fi
        sleep 1
      done
    else
      sleep 2
    fi
  fi
  log "Postgres ready at localhost:$POSTGRES_PORT"
}

start_redis() {
  info "Starting Redis ($REDIS_IMAGE) on port $REDIS_PORT..."
  ensure_network_exists
  if docker ps -a --format '{{.Names}} {{.Status}}' | grep -E "^${REDIS_CONTAINER} " >/dev/null 2>&1; then
    local status
    status="$(docker ps -a --format '{{.Names}} {{.Status}}' | awk "/^${REDIS_CONTAINER} /{print substr($0, index($0,$2))}")"
    if echo "$status" | grep -qi "Up"; then
      info "Container ${REDIS_CONTAINER} is already running."
      REDIS_MODE="container"
    else
      info "Starting existing container ${REDIS_CONTAINER}..."
      docker start "$REDIS_CONTAINER" >/dev/null
      REDIS_MODE="container"
    fi
  else
    if port_in_use "$REDIS_PORT"; then
      local owner; owner="$(port_owner_cmd "$REDIS_PORT" || true)"
      info "Detected existing Redis (or another service) on port $REDIS_PORT (owner: ${owner:-unknown}). Will reuse external Redis and skip creating ${REDIS_CONTAINER}."
      REDIS_MODE="external"
    else
      info "Creating container ${REDIS_CONTAINER}..."
      docker run -d \
        --name "$REDIS_CONTAINER" \
        --restart unless-stopped \
        --network "$DOCKER_NETWORK" \
        -p "$REDIS_PORT:6379" \
        "$REDIS_IMAGE" >/dev/null
      REDIS_MODE="container"
    fi
  fi

  info "Waiting for Redis to become ready..."
  local tries=0
  if [ "$REDIS_MODE" = "container" ]; then
    until docker exec "$REDIS_CONTAINER" redis-cli ping >/dev/null 2>&1; do
      tries=$((tries+1))
      if [ "$tries" -gt 60 ]; then
        err "Redis (container) did not become ready in time."
        exit 1
      fi
      sleep 1
    done
  else
    if command -v nc >/dev/null 2>&1; then
      until nc -z 127.0.0.1 "$REDIS_PORT" >/dev/null 2>&1; do
        tries=$((tries+1))
        if [ "$tries" -gt 60 ]; then
          err "External Redis on port $REDIS_PORT is not reachable."
          exit 1
        fi
        sleep 1
      done
    else
      sleep 2
    fi
  fi
  log "Redis ready (${REDIS_MODE}) at localhost:$REDIS_PORT"
}

start_backend() {
  info "Starting Backend on port $BACKEND_PORT..."
  if ! port_in_use "$BACKEND_PORT"; then
    (
      cd backend
      # Python venv
      if [ ! -d .venv ]; then
        info "Creating backend venv..."
        python3 -m venv .venv
      fi
      . .venv/bin/activate
      pip install -U pip >/dev/null
      pip install -r requirements.txt >/dev/null
      # Ensure DATABASE_URL is set to dockerized Postgres if not provided
      if [ -z "${DATABASE_URL:-}" ]; then
        export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${POSTGRES_PORT}/${POSTGRES_DB}"
        info "DATABASE_URL not set; using ${DATABASE_URL}"
      fi
      # Ensure Agent base url follows SSOT (used by backend service to reach Agent)
      export AGENT_BASE_URL="${AGENT_BASE_URL:-http://127.0.0.1:${AGENT_PORT}}"
      info "Launching backend..."
      nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" > backend.log 2>&1 &
    )
    # Wait for health
    local tries=0
    until curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/v1/health" >/dev/null 2>&1; do
      tries=$((tries+1))
      if [ "$tries" -gt 60 ]; then
        err "Backend did not become healthy in time."
        exit 1
      fi
      sleep 1
    done
    log "Backend ready at http://127.0.0.1:${BACKEND_PORT}"
  else
    info "Backend already running on port $BACKEND_PORT. Reusing instance."
  fi
}

build_and_start_agent() {
  info "Building/Preparing Agent image ($AGENT_IMAGE)..."
  local need_build=0
  if [ "${FORCE_BUILD:-0}" = "1" ]; then
    need_build=1
  elif ! docker image inspect "$AGENT_IMAGE" >/dev/null 2>&1; then
    need_build=1
  fi

  if [ "$need_build" -eq 1 ]; then
    info "Building Agent image..."
    if ! docker build -t "$AGENT_IMAGE" "$PROJECT_ROOT/agent"; then
      err "Failed to build agent image. If you're behind a corporate proxy/SSL inspection, ensure Docker trusts your corporate root CA or configure the proxy, then retry."
      exit 1
    fi
  else
    info "Using existing image $AGENT_IMAGE (set FORCE_BUILD=1 to rebuild)."
  fi

  info "Starting Agent container on port $AGENT_PORT..."
  if docker ps -a --format '{{.Names}}' | grep -q "^${AGENT_CONTAINER}$"; then
    info "Removing existing container ${AGENT_CONTAINER}..."
    docker rm -f "$AGENT_CONTAINER" >/dev/null 2>&1 || true
  fi
  ensure_network_exists
  if port_in_use "$AGENT_PORT"; then
    local owner; owner="$(port_owner_cmd "$AGENT_PORT" || true)"
    err "Port $AGENT_PORT is occupied by ${owner:-unknown}. Cannot start Agent. Please free the port."
    exit 1
  fi

  # Resolve Redis URL for Agent based on mode
  local AGENT_REDIS_URL
  if [ "$REDIS_MODE" = "container" ]; then
    AGENT_REDIS_URL="${REDIS_URL:-redis://bp-redis:6379/0}"
  else
    # Use host.docker.internal to reach host Redis from container (Docker Desktop)
    AGENT_REDIS_URL="${REDIS_URL:-redis://host.docker.internal:${REDIS_PORT}/0}"
  fi

  # Compute database URL for Agent inside container
  local AGENT_DATABASE_URL
  if docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    # Reach Postgres container via docker network by its container name
    AGENT_DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_CONTAINER}:5432/${POSTGRES_DB}"
  else
    # Reach host Postgres via host.docker.internal
    AGENT_DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@host.docker.internal:${POSTGRES_PORT}/${POSTGRES_DB}"
  fi

  docker run -d \
    --name "$AGENT_CONTAINER" \
    --restart unless-stopped \
    --network "$DOCKER_NETWORK" \
    --env-file "$PROJECT_ROOT/.env" \
    -e REDIS_URL="$AGENT_REDIS_URL" \
    -e AGENT_DATABASE_URL="$AGENT_DATABASE_URL" \
    -p "$AGENT_PORT:2024" \
    "$AGENT_IMAGE" >/dev/null

  # Wait for health
  local tries=0
  until curl -fsS "http://127.0.0.1:${AGENT_PORT}/health" >/dev/null 2>&1; do
    tries=$((tries+1))
    if [ "$tries" -gt 60 ]; then
      err "Agent did not become healthy in time."
      exit 1
    fi
    sleep 1
  done
  log "Agent ready at http://127.0.0.1:${AGENT_PORT}"
}

start_frontend() {
  info "Starting Frontend (Vite) on port $FRONTEND_PORT..."
  if ! port_in_use "$FRONTEND_PORT"; then
    (
      cd frontend
      if [ -f package-lock.json ]; then
        npm ci >/dev/null
      else
        npm install >/dev/null
      fi
      info "Launching frontend dev server..."
      # Propagate SSOT ports to Vite dev server environment
      export VITE_BACKEND_PORT="$BACKEND_PORT"
      export VITE_DEV_PORT="$FRONTEND_PORT"
      nohup env VITE_BACKEND_PORT="$BACKEND_PORT" VITE_DEV_PORT="$FRONTEND_PORT" npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" > dev.log 2>&1 &
    )
    # Health check for frontend dev server
    local tries=0
    until curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/" >/dev/null 2>&1; do
      tries=$((tries+1))
      if [ "$tries" -gt 60 ]; then
        err "Frontend did not become ready in time."
        exit 1
      fi
      sleep 1
    done
    log "Frontend ready at http://127.0.0.1:${FRONTEND_PORT}/"
  else
    info "Frontend already running on port $FRONTEND_PORT. Reusing instance."
  fi
}

# --- Start sequence: DB -> Redis -> Backend -> Agent -> Frontend ---
start_postgres
start_redis
start_backend
build_and_start_agent
start_frontend

info "All services started."
# Use safe printing to avoid printf interpreting leading '-' as options
printf "%s\n" "" "Endpoints:" \
  "- Backend:  http://127.0.0.1:${BACKEND_PORT}/api/v1/health" \
  "- Agent:    http://127.0.0.1:${AGENT_PORT}/health" \
  "- Redis:    redis://127.0.0.1:${REDIS_PORT}/0 (${REDIS_MODE})" \
  "- Frontend: http://127.0.0.1:${FRONTEND_PORT}/" ""

exit 0