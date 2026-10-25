#!/usr/bin/env bash
set -e

echo "=========================================="
echo " Starting Net-AIOps Studio (Full-Stack)   "
echo "=========================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT_DIR/logs"

# 1. Start Backend (FastAPI on Port 3001)
echo "[1/2] Launching FastAPI Backend on http://127.0.0.1:3001..."
cd "$ROOT_DIR/backend"
if [ ! -d ".venv" ]; then
    echo "Creating python uv venv..."
    uv venv --python 3.12 .venv
    uv pip install -e .
fi
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload &
BACKEND_PID=$!

# Trap exit signals to terminate both processes cleanly
cleanup() {
    echo "Shutting down Net-AIOps Studio..."
    kill $BACKEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Wait a second for backend to initialize
sleep 2

# 2. Start Frontend (Next.js on Port 3000)
echo "[2/2] Launching Next.js Frontend on http://127.0.0.1:3000..."
cd "$ROOT_DIR/frontend"
npm run dev

wait
