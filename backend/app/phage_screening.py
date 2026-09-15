from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any
from zipfile import ZipFile

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .phage_catalog import DATA_DIR, validate_phage_catalog
from .real_cocktail import ReviewedPhageMetadata
from .safety import GenomicSafetyEvidence, evaluate_genomic_safety

EVIDENCE_PATH = DATA_DIR / "reviewed_evidence.json"
REQUIRED_SCREENS = (
    "lysogeny_screen_passed", "toxin_screen_passed", "virulence_screen_passed",
    "amr_screen_passed", "contamination_screen_passed", "assembly_qc_passed",
)
CURRENT_EVIDENCE_SCHEMA_VERSION = 1
EVIDENCE_POLICY = "Only independently reviewed evidence may make a phage cocktail-eligible."


class ReviewedEvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    phage_id: str = Field(min_length=1, max_length=100)
    family: str = Field(min_length=1, max_length=100)
    receptor: str = Field(min_length=1, max_length=100)
    submitter: str = Field(min_length=1, max_length=200)
    reviewer: str = Field(min_length=1, max_length=200)
    source_digest: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    lysogeny_screen_passed: bool
    toxin_screen_passed: bool
    virulence_screen_passed: bool
    amr_screen_passed: bool
    contamination_screen_passed: bool
    assembly_qc_passed: bool


class ReviewedEvidenceRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: int
    policy: str = Field(min_length=1)
    records: list[ReviewedEvidenceRecord]


def migrate_evidence_registry(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the current in-memory schema; callers decide whether to persist it."""
    version = payload.get("schema_version", 0)
    if version == 0:
        migrated = dict(payload)
        migrated["schema_version"] = 1
        migrated.setdefault("policy", EVIDENCE_POLICY)
        migrated.setdefault("records", [])
        return migrated
    if version == CURRENT_EVIDENCE_SCHEMA_VERSION:
        return payload
    if isinstance(version, int) and version > CURRENT_EVIDENCE_SCHEMA_VERSION:
        raise RuntimeError(f"Reviewed evidence schema {version} is newer than this application supports")
    raise RuntimeError(f"Reviewed evidence schema {version!r} has no migration path")


def _sequence_for(phage_id: str) -> str:
    validate_phage_catalog()
    with ZipFile(DATA_DIR / "phages_genomes.zip") as archive:
        matches = [name for name in archive.namelist() if name.endswith(f"/{phage_id}.fasta") and not name.startswith("__MACOSX/")]
        if len(matches) != 1:
            raise KeyError(phage_id)
        text = archive.read(matches[0]).decode("utf-8")
    return "".join(line.strip().upper() for line in text.splitlines() if not line.startswith(">"))


def genome_qc(phage_id: str) -> dict[str, Any]:
    sequence = _sequence_for(phage_id)
    valid = sum(base in "ACGT" for base in sequence)
    gc = sum(base in "GC" for base in sequence)
    ambiguous = len(sequence) - valid
    warnings = []
    if len(sequence) < 10_000:
        warnings.append("genome shorter than the minimum research QC threshold")
    if ambiguous / len(sequence) > 0.01:
        warnings.append("more than 1% ambiguous bases")
    return {
        "phage_id": phage_id,
        "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
        "length_bp": len(sequence),
        "gc_fraction": round(gc / len(sequence), 6),
        "ambiguous_fraction": round(ambiguous / len(sequence), 6),
        "assembly_qc_status": "pass" if not warnings else "review-required",
        "warnings": warnings,
        "interpretation": "Sequence QC only; it is not biological safety clearance.",
    }


def load_reviewed_metadata() -> list[ReviewedPhageMetadata]:
    raw_payload = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw_payload, dict):
        raise RuntimeError("Reviewed evidence registry must be a JSON object")
    try:
        payload = ReviewedEvidenceRegistry.model_validate(migrate_evidence_registry(raw_payload))
    except ValidationError as error:
        raise RuntimeError(f"Reviewed evidence registry failed schema validation: {error.errors()[0]['msg']}") from error
    if payload.schema_version != CURRENT_EVIDENCE_SCHEMA_VERSION:
        raise RuntimeError("Reviewed evidence registry has an unsupported schema")
    seen: set[str] = set()
    records = []
    for item in payload.records:
        phage_id = item.phage_id
        if phage_id in seen:
            raise RuntimeError(f"Duplicate reviewed evidence for {phage_id}")
        seen.add(phage_id)
        if item.submitter == item.reviewer:
            raise RuntimeError(f"Evidence for {phage_id} lacks independent review")
        evidence = GenomicSafetyEvidence(
            **{key: getattr(item, key) for key in REQUIRED_SCREENS},
            source_digest=item.source_digest, reviewer=item.reviewer,
        )
        records.append(ReviewedPhageMetadata(phage_id=phage_id, family=item.family, receptor=item.receptor, safety=evidence))
    return records


def evidence_status(phage_id: str) -> dict[str, Any]:
    qc = genome_qc(phage_id)
    record = next((item for item in load_reviewed_metadata() if item.phage_id == phage_id), None)
    if record is None:
        return {**qc, "evidence_status": "not-reviewed", "cocktail_eligible": False, "family": None, "receptor": None,
                "blockers": ["missing independently reviewed family/receptor metadata", "missing independently reviewed genomic safety evidence"],
                "required_screens": list(REQUIRED_SCREENS)}
    gate = evaluate_genomic_safety(record.safety)
    blockers = list(gate.blockers)
    if not record.family or not record.receptor:
        blockers.append("missing reviewed family or receptor")
    return {**qc, "evidence_status": gate.status, "cocktail_eligible": not blockers, "family": record.family or None,
            "receptor": record.receptor or None, "blockers": blockers, "required_screens": list(REQUIRED_SCREENS),
            "reviewed_evidence": asdict(record.safety)}


def registry_status() -> dict[str, Any]:
    catalog = validate_phage_catalog()
    reviewed = load_reviewed_metadata()
    eligible = sum(evaluate_genomic_safety(item.safety).eligible and bool(item.family and item.receptor) for item in reviewed)
    return {"catalog_phages": catalog["phage_genomes"], "reviewed_records": len(reviewed), "cocktail_eligible_records": eligible,
            "policy": "fail-closed-independent-review", "required_screens": list(REQUIRED_SCREENS),
            "disclaimer": "Research evidence workflow only; laboratory validation remains required."}
