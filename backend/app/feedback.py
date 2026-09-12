import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .schemas import LabObservationRequest, LabObservationResponse


SCHEMA = """
CREATE TABLE IF NOT EXISTS lab_observations (
    observation_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    analysis_id TEXT NOT NULL,
    phage_id TEXT NOT NULL,
    assay_type TEXT NOT NULL,
    outcome TEXT NOT NULL,
    measured_value REAL,
    units TEXT,
    research_only INTEGER NOT NULL CHECK (research_only = 1)
)
"""


class LabObservationStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def add(self, observation: LabObservationRequest) -> LabObservationResponse:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        observation_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(SCHEMA)
            connection.execute(
                """
                INSERT INTO lab_observations (
                    observation_id, created_at, analysis_id, phage_id, assay_type,
                    outcome, measured_value, units, research_only
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    observation_id,
                    created_at,
                    observation.analysis_id,
                    observation.phage_id,
                    observation.assay_type,
                    observation.outcome,
                    observation.measured_value,
                    observation.units,
                ),
            )
        return LabObservationResponse(
            observation_id=observation_id,
            created_at=created_at,
            status="recorded-research-observation",
        )

