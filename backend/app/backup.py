from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_databases(sources: list[Path], destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    records = []
    for source in sources:
        if not source.is_file():
            continue
        target = destination / source.name
        with sqlite3.connect(source) as source_db, sqlite3.connect(target) as target_db:
            source_db.backup(target_db)
        integrity = sqlite3.connect(target).execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Backup integrity check failed for {source.name}")
        records.append({"filename": source.name, "sha256": _sha256(target), "integrity_check": integrity})
    manifest = destination / "backup_manifest.json"
    manifest.write_text(json.dumps({"created_at": datetime.now(timezone.utc).isoformat(), "files": records}, indent=2) + "\n")
    return manifest


def verify_backup(directory: Path) -> dict:
    manifest = json.loads((directory / "backup_manifest.json").read_text())
    for record in manifest["files"]:
        path = directory / record["filename"]
        if not path.is_file() or _sha256(path) != record["sha256"]:
            raise RuntimeError(f"Backup digest mismatch: {record['filename']}")
        with sqlite3.connect(path) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError(f"Backup database is corrupt: {record['filename']}")
    return {"status": "verified", "files": len(manifest["files"]), "created_at": manifest["created_at"]}
