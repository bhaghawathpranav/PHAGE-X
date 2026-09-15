#!/usr/bin/env python3
"""Validate and explicitly migrate a reviewed-evidence registry copy."""

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.phage_screening import ReviewedEvidenceRegistry, migrate_evidence_registry  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Existing registry JSON")
    parser.add_argument("output", type=Path, help="New path for the validated current-schema copy")
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise SystemExit("Refusing to overwrite the source registry; choose a separate output path")
    payload = json.loads(args.source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("Registry root must be a JSON object")
    validated = ReviewedEvidenceRegistry.model_validate(migrate_evidence_registry(payload))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(validated.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"wrote schema {validated.schema_version} registry to {args.output}")


if __name__ == "__main__":
    main()
