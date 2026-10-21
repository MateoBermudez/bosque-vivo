import threading
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from bosquevivo.core.logging import get_logger
from bosquevivo.jobs.queue import JobQueue

log = get_logger(__name__)

Handler = Callable[[Session, dict[str, Any]], dict[str, Any] | None]


class JobWorker:
    def __init__(self, factory: sessionmaker[Session], poll_seconds: float = 1.0) -> None:
        self.factory = factory
        self.poll_seconds = poll_seconds
        self.handlers: dict[str, Handler] = {}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def register(self, kind: str, handler: Handler) -> None:
        self.handlers[kind] = handler

    def run_once(self) -> bool:
        with self.factory() as session:
            queue = JobQueue(session)
            job = queue.claim_next()
            if job is None:
                return False
            session.commit()
            handler = self.handlers.get(job.kind)
            if handler is None:
                queue.fail(job, f"sin manejador para {job.kind}")
                session.commit()
                return True
            try:
                result = handler(session, job.payload)
                queue.complete(job, result)
            except Exception as exc:
                session.rollback()
                log.error("job_failed", kind=job.kind, job_id=job.id, error=str(exc))
                job = queue.get(job.id) or job
                queue.fail(job, str(exc))
            session.commit()
            return True

    def drain(self) -> int:
        count = 0
        while self.run_once():
            count += 1
        return count

    def _loop(self) -> None:
        while not self._stop.is_set():
            if not self.run_once():
                self._stop.wait(self.poll_seconds)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="job-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
