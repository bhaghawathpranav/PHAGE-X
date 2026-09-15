import pytest

from app import inference
from app.data import load_demo_data
from app.phage_screening import (
    CURRENT_EVIDENCE_SCHEMA_VERSION,
    ReviewedEvidenceRegistry,
    migrate_evidence_registry,
)


def test_demo_data_is_cached_per_process():
    load_demo_data.cache_clear()
    first = load_demo_data()
    second = load_demo_data()
    assert first is second
    assert load_demo_data.cache_info().hits == 1


def test_demo_cocktail_search_rejects_catalog_above_bound(monkeypatch):
    data = load_demo_data()
    isolate = data["isolates"][0]
    monkeypatch.setattr(inference, "MAX_EXHAUSTIVE_COCKTAIL_CANDIDATES", 2)
    with pytest.raises(ValueError, match="prefilter the catalog"):
        inference.analyze(isolate, data["phages"], 3, "preloaded")


def test_legacy_empty_evidence_registry_has_explicit_migration():
    migrated = migrate_evidence_registry({"records": []})
    assert migrated["schema_version"] == CURRENT_EVIDENCE_SCHEMA_VERSION
    assert ReviewedEvidenceRegistry.model_validate(migrated).records == []


def test_future_evidence_schema_fails_closed():
    with pytest.raises(RuntimeError, match="newer than this application supports"):
        migrate_evidence_registry({"schema_version": CURRENT_EVIDENCE_SCHEMA_VERSION + 1, "records": []})
