#!/usr/bin/env python3
"""Download the pinned ESM-2 files for offline feature extraction."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "backend" / "data" / "esm2" / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path.home() / ".cache" / "torch" / "hub" / "checkpoints",
    )
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    for item in manifest["files"]:
        destination = args.checkpoint_dir / item["filename"]
        if destination.is_file() and sha256(destination) == item["sha256"]:
            print(f"verified {destination.name}")
            continue
        with tempfile.NamedTemporaryFile(dir=args.checkpoint_dir, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            try:
                with urllib.request.urlopen(item["url"], timeout=60) as response:
                    shutil.copyfileobj(response, temporary)
            except Exception:
                temporary_path.unlink(missing_ok=True)
                raise
        if sha256(temporary_path) != item["sha256"]:
            temporary_path.unlink(missing_ok=True)
            raise RuntimeError(f"Checksum verification failed for {item['filename']}")
        os.replace(temporary_path, destination)
        print(f"downloaded and verified {destination.name}")


if __name__ == "__main__":
    main()
