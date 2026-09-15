#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$repo_dir/.venv/bin/python"

if [[ ! -x "$python_bin" ]]; then
  echo "Missing .venv. Run: python3 -m venv .venv"
  exit 1
fi

"$python_bin" -m pip install -r "$repo_dir/backend/requirements-ml.txt"
"$python_bin" "$repo_dir/scripts/fetch_phagehostlearn.py" \
  --destination "$repo_dir/work/phagehostlearn"

PYTHONPATH="$repo_dir/backend" "$python_bin" -m ml.train \
  --data-dir "$repo_dir/work/phagehostlearn" \
  --manifest "$repo_dir/data/phagehostlearn/manifest.json" \
  --output-dir "$repo_dir/backend/artifacts" \
  --repeats "${PHAGEX_EVAL_REPEATS:-5}" \
  | tee "$repo_dir/work/latest-training-report.json"

echo
echo "Model:      $repo_dir/backend/artifacts/model.joblib"
echo "Metrics:    $repo_dir/backend/artifacts/model_card.json"
echo "Full log:   $repo_dir/work/latest-training-report.json"
