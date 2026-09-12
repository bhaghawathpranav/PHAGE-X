from pathlib import Path

import pytest

from ml.registry import verify_release_manifest, write_release_manifest


def test_release_manifest_detects_artifact_change(tmp_path: Path):
    model = tmp_path / "model.joblib"
    card = tmp_path / "model_card.json"
    manifest = tmp_path / "release_manifest.json"
    model.write_bytes(b"model-v1")
    card.write_text("{}")
    write_release_manifest(model, card, manifest)
    verify_release_manifest(tmp_path, manifest)
    model.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="verification failed"):
        verify_release_manifest(tmp_path, manifest)
