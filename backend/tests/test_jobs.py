import threading

import pytest

from app.jobs import BoundedJobManager


def test_job_runs_and_returns_result():
    manager = BoundedJobManager(max_workers=1, max_queued=0)
    record = manager.submit(lambda: {"answer": 42})
    record.future.result(timeout=2)
    assert manager.get(record.job_id).status == "succeeded"
    assert manager.get(record.job_id).result == {"answer": 42}
    assert manager.stats()["succeeded"] == 1


def test_queue_capacity_fails_closed():
    gate = threading.Event()
    manager = BoundedJobManager(max_workers=1, max_queued=0)
    first = manager.submit(lambda: gate.wait(2) or {})
    with pytest.raises(RuntimeError, match="queue is full"):
        manager.submit(lambda: {})
    gate.set()
    first.future.result(timeout=2)


def test_queued_job_can_be_cancelled():
    gate = threading.Event()
    manager = BoundedJobManager(max_workers=1, max_queued=1)
    running = manager.submit(lambda: gate.wait(2) or {})
    queued = manager.submit(lambda: {"should_not": "run"})
    cancelled = manager.cancel(queued.job_id)
    assert cancelled.status == "cancelled"
    assert cancelled.result is None
    gate.set()
    running.future.result(timeout=2)
