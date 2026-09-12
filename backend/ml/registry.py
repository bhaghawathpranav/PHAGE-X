import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_release_manifest(model_path: Path, model_card_path: Path, output_path: Path, *extra_paths: Path) -> Dict[str, object]:
    release = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "artifacts": {
            model_path.name: sha256(model_path),
            model_card_path.name: sha256(model_card_path),
        },
    }
    for path in extra_paths:
        release["artifacts"][path.name] = sha256(path)
    output_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    return release


def verify_release_manifest(directory: Path, manifest_path: Path) -> None:
    release = json.loads(manifest_path.read_text(encoding="utf-8"))
    for filename, expected in release["artifacts"].items():
        artifact = directory / filename
        if not artifact.exists() or sha256(artifact) != expected:
            raise ValueError(f"Artifact verification failed: {filename}")
