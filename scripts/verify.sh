#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -x "$repo_dir/.venv/bin/pytest" ]]; then
  echo "Backend test dependencies are missing. Follow the setup instructions in README.md."
  exit 1
fi

if [[ ! -d "$repo_dir/frontend/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run npm ci in frontend/."
  exit 1
fi

echo "Running backend tests..."
(cd "$repo_dir/backend" && PHAGEX_RUN_REAL_PIPELINE=0 ../.venv/bin/pytest -q)

echo "Building the frontend..."
(cd "$repo_dir/frontend" && npm run build)

if [[ "${PHAGEX_RUN_REAL_PIPELINE:-0}" == "1" ]]; then
  echo "Running the real FASTA acceptance path..."
  (cd "$repo_dir" && PHAGEX_RUN_REAL_PIPELINE=1 PYTHONPATH=backend \
    .venv/bin/pytest -q backend/tests/test_real_pipeline_acceptance.py -vv)
fi

echo "PHAGE-X verification complete."
