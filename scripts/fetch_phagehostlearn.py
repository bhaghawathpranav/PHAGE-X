#!/usr/bin/env python3
"""Fetch the pinned public PhageHostLearn subset and verify every byte."""

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "data" / "phagehostlearn" / "manifest.json"


def digest(path: Path) -> str:
    checksum = hashlib.md5()  # nosec B324: integrity value published by source dataset
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def fetch(destination: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    destination.mkdir(parents=True, exist_ok=True)
    for record in manifest["files"]:
        target = destination / record["name"]
        if target.exists() and target.stat().st_size == record["bytes"] and digest(target) == record["md5"]:
            print(f"verified {target.name}")
            continue
        partial = target.with_suffix(target.suffix + ".partial")
        print(f"downloading {target.name}")
        urllib.request.urlretrieve(record["url"], partial)
        if partial.stat().st_size != record["bytes"] or digest(partial) != record["md5"]:
            partial.unlink(missing_ok=True)
            raise RuntimeError(f"Integrity verification failed for {target.name}")
        partial.replace(target)
        print(f"verified {target.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=REPO / "work" / "phagehostlearn")
    args = parser.parse_args()
    fetch(args.destination)

