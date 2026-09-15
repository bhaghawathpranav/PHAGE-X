#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -x "$repo_dir/.venv/bin/uvicorn" || ! -d "$repo_dir/frontend/node_modules" ]]; then
  echo "Install dependencies first; see README.md."
  exit 1
fi

cleanup() { kill "$api_pid" "$ui_pid" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

(cd "$repo_dir/backend" && "$repo_dir/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000) &
api_pid=$!
(cd "$repo_dir/frontend" && npm run dev -- --host 127.0.0.1) &
ui_pid=$!

echo "PHAGE-X is starting at http://localhost:5173"
echo "Press Ctrl-C to stop both services."
wait
