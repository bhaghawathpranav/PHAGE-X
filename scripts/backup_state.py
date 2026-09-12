from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from app.backup import backup_databases, verify_backup

parser = argparse.ArgumentParser(description="Create and verify a PHAGE-X metadata backup.")
parser.add_argument("--work-dir", type=Path, default=Path("work"))
parser.add_argument("--output-dir", type=Path, default=Path("backups"))
args = parser.parse_args()

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
target = args.output_dir / f"phagex-{stamp}"
manifest = backup_databases(
    [args.work_dir / "phagex_feedback.sqlite3", args.work_dir / "phagex_audit.sqlite3", args.work_dir / "esm2_embeddings.sqlite3"], target,
)
print(manifest)
print(verify_backup(target))
