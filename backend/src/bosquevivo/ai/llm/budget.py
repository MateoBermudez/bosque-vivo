import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from bosquevivo.core.errors import ExternalServiceError

_DEADLINE: ContextVar[float | None] = ContextVar("llm_deadline", default=None)


class TimeBudgetExceededError(ExternalServiceError):
    code = 0


@contextmanager
def time_budget(seconds: float | None) -> Iterator[None]:
    token = _DEADLINE.set(time.monotonic() + seconds if seconds and seconds > 0 else None)
    try:
        yield
    finally:
        _DEADLINE.reset(token)


def remaining_seconds() -> float | None:
    deadline = _DEADLINE.get()
    return None if deadline is None else deadline - time.monotonic()
