import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from bosquevivo.db import init_db, make_session_factory
from bosquevivo.db.models import Job
from bosquevivo.jobs import JobQueue, JobWorker


@pytest.fixture
def factory() -> sessionmaker:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    init_db(engine)
    return make_session_factory(engine)


def enqueue(factory, kind="echo", payload=None):
    with factory() as s:
        job = JobQueue(s).enqueue(kind, payload or {"n": 1})
        s.commit()
        return job.id


def test_job_runs_and_stores_result(factory):
    worker = JobWorker(factory)
    worker.register("echo", lambda session, payload: {"echo": payload["n"]})
    job_id = enqueue(factory)
    assert worker.drain() == 1
    with factory() as s:
        job = s.get(Job, job_id)
        assert job.status == "done"
        assert job.result == {"echo": 1}


def test_failing_job_is_retried_then_marked_failed(factory):
    worker = JobWorker(factory)

    def boom(session, payload):
        raise RuntimeError("falló")

    worker.register("boom", boom)
    job_id = enqueue(factory, "boom")
    assert worker.drain() == 3
    with factory() as s:
        job = s.get(Job, job_id)
        assert job.status == "failed"
        assert job.attempts == 3
        assert "falló" in job.error


def test_unknown_kind_fails(factory):
    worker = JobWorker(factory)
    job_id = enqueue(factory, "desconocido")
    worker.drain()
    with factory() as s:
        assert s.get(Job, job_id).status == "failed"


def test_jobs_are_processed_in_order(factory):
    seen = []
    worker = JobWorker(factory)
    worker.register("echo", lambda session, payload: seen.append(payload["n"]))
    for n in (1, 2, 3):
        enqueue(factory, payload={"n": n})
    worker.drain()
    assert seen == [1, 2, 3]
