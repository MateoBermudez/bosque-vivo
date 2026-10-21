import pytest

from bosquevivo.ai.llm import LLMResponse, Message, QuotaExceededError, ScriptedLLM, ToolCall
from bosquevivo.ai.llm.cache import ResponseCache, request_key
from bosquevivo.ai.llm.gemini import GeminiProvider
from bosquevivo.ai.llm.limits import RateLimiter
from bosquevivo.core.errors import ExternalServiceError


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_rate_limiter_blocks_after_per_minute_limit():
    clock = Clock()
    limiter = RateLimiter(per_minute=2, per_day=100, clock=clock)
    limiter.acquire()
    limiter.acquire()
    with pytest.raises(QuotaExceededError):
        limiter.acquire()


def test_rate_limiter_recovers_after_a_minute():
    clock = Clock()
    limiter = RateLimiter(per_minute=1, per_day=100, clock=clock)
    limiter.acquire()
    clock.now = 61
    limiter.acquire()
    assert limiter.used_today == 2


def test_rate_limiter_enforces_daily_limit():
    clock = Clock()
    limiter = RateLimiter(per_minute=100, per_day=2, clock=clock)
    limiter.acquire()
    clock.now = 100
    limiter.acquire()
    clock.now = 200
    with pytest.raises(QuotaExceededError):
        limiter.acquire()


def test_cache_roundtrip_keeps_text_and_tool_calls(tmp_path):
    cache = ResponseCache(tmp_path)
    key = request_key("m", "sys", [{"a": 1}], None)
    assert cache.get(key) is None
    cache.put(key, LLMResponse(text="hola", tool_calls=[ToolCall("t", {"x": 1})]))
    hit = cache.get(key)
    assert hit is not None and hit.text == "hola" and hit.tool_calls[0].args == {"x": 1}


def test_cache_ignores_blocked_responses(tmp_path):
    cache = ResponseCache(tmp_path)
    cache.put("k", LLMResponse(blocked=True))
    assert cache.get("k") is None


def test_request_key_changes_with_input():
    assert request_key("m", "s", [{"a": 1}], None) != request_key("m", "s", [{"a": 2}], None)


def test_scripted_llm_returns_in_order_and_blocks_when_exhausted():
    llm = ScriptedLLM([LLMResponse(text="uno")])
    assert llm.generate("s", [Message(role="user", text="x")]).text == "uno"
    assert llm.generate("s", [Message(role="user", text="x")]).blocked


def test_gemini_requires_credentials():
    with pytest.raises(ExternalServiceError):
        GeminiProvider("", "")
