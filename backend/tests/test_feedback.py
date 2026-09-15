import sqlite3
from pathlib import Path

from app.feedback import LabObservationStore
from app.schemas import LabObservationRequest


def test_lab_observation_is_append_only_research_record(tmp_path: Path):
    database = tmp_path / "feedback.sqlite3"
    result = LabObservationStore(database).add(
        LabObservationRequest(
            analysis_id="analysis-123",
            phage_id="phage-7",
            assay_type="plaque_assay",
            outcome="susceptible",
            measured_value=0.8,
            units="relative EOP",
        )
    )
    assert result.status == "recorded-research-observation"
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT outcome, research_only FROM lab_observations WHERE observation_id = ?",
            (result.observation_id,),
        ).fetchone()
    assert row == ("susceptible", 1)

