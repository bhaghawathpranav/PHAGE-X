from __future__ import annotations

import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict


@dataclass
class JobRecord:
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    result: dict | None = None
    error: str | None = None
    cancel_requested: bool = False
    future: Future | None = field(default=None, repr=False)


class BoundedJobManager:
    def __init__(self, max_workers: int = 1, max_queued: int = 2, retention_minutes: int = 60):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="phagex-feature")
        self.capacity = threading.BoundedSemaphore(max_workers + max_queued)
        self.retention = timedelta(minutes=retention_minutes)
        self.records: Dict[str, JobRecord] = {}
        self.lock = threading.Lock()

    def submit(self, task: Callable[[], dict]) -> JobRecord:
        self.prune()
        if not self.capacity.acquire(blocking=False):
            raise RuntimeError("Feature-extraction queue is full; retry later")
        now = datetime.now(timezone.utc)
        record = JobRecord(str(uuid.uuid4()), "queued", now, now)
        with self.lock:
            self.records[record.job_id] = record

        def run() -> None:
            try:
                with self.lock:
                    if record.cancel_requested:
                        record.status = "cancelled"
                        record.updated_at = datetime.now(timezone.utc)
                        return
                    record.status = "running"
                    record.updated_at = datetime.now(timezone.utc)
                result = task()
                with self.lock:
                    record.status = "cancelled" if record.cancel_requested else "succeeded"
                    record.result = None if record.cancel_requested else result
                    record.updated_at = datetime.now(timezone.utc)
            except Exception as error:
                with self.lock:
                    record.status = "failed"
                    record.error = str(error)[:500]
                    record.updated_at = datetime.now(timezone.utc)
            finally:
                self.capacity.release()

        record.future = self.executor.submit(run)
        return record

    def get(self, job_id: str) -> JobRecord:
        self.prune()
        with self.lock:
            if job_id not in self.records:
                raise KeyError(job_id)
            return self.records[job_id]

    def cancel(self, job_id: str) -> JobRecord:
        record = self.get(job_id)
        with self.lock:
            if record.status in {"succeeded", "failed", "cancelled"}:
                return record
            record.cancel_requested = True
            if record.future and record.future.cancel():
                record.status = "cancelled"
                record.updated_at = datetime.now(timezone.utc)
                self.capacity.release()
            return record

    def prune(self) -> None:
        cutoff = datetime.now(timezone.utc) - self.retention
        with self.lock:
            expired = [
                job_id for job_id, record in self.records.items()
                if record.status in {"succeeded", "failed", "cancelled"} and record.updated_at < cutoff
            ]
            for job_id in expired:
                del self.records[job_id]

    def stats(self) -> Dict[str, int]:
        self.prune()
        with self.lock:
            counts = {status: 0 for status in ("queued", "running", "succeeded", "failed", "cancelled")}
            for record in self.records.values():
                counts[record.status] += 1
            return counts


def serialize_job(record: JobRecord) -> dict:
    return {
        "job_id": record.job_id,
        "status": record.status,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
        "result": record.result,
        "error": record.error,
        "cancel_requested": record.cancel_requested,
    }
