from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors as genai_errors

from bosquevivo.ai.llm import LLMResponse, Message, QuotaExceededError, ScriptedLLM, ToolCall
from bosquevivo.ai.llm.budget import TimeBudgetExceededError, remaining_seconds, time_budget
from bosquevivo.ai.llm.cache import ResponseCache, request_key
from bosquevivo.ai.llm.gemini import _COOLING, GeminiProvider
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


def test_overloaded_model_switches_to_another_free_model(monkeypatch):
    calls = []

    class Models:
        def generate_content(self, model, contents, config):
            calls.append(model)
            if model == "gemini-flash-latest":
                raise genai_errors.APIError(503, {"error": {"message": "high demand"}})
            part = SimpleNamespace(text="hola", function_call=None, thought=None)
            candidate = SimpleNamespace(content=SimpleNamespace(parts=[part]), finish_reason=None)
            return SimpleNamespace(
                candidates=[candidate], prompt_feedback=None, usage_metadata=None
            )

    _COOLING.clear()
    now = [1000.0]
    provider = GeminiProvider(
        "clave",
        "gemini-flash-latest",
        light_model="gemini-flash-lite-latest",
        sleep=lambda _: None,
        client=SimpleNamespace(models=Models()),
        clock=lambda: now[0],
    )
    response = provider.generate("sistema", [Message(role="user", text="hola")])
    assert response.text == "hola"
    assert calls == ["gemini-flash-latest", "gemini-flash-lite-latest"]
    provider.generate("sistema", [Message(role="user", text="otra")])
    assert calls[-1] == "gemini-flash-lite-latest" and len(calls) == 3
    now[0] += 200
    provider.generate("sistema", [Message(role="user", text="tercera")])
    assert calls[-2:] == ["gemini-flash-latest", "gemini-flash-lite-latest"]
    _COOLING.clear()


def _ok_response():
    part = SimpleNamespace(text="hola", function_call=None, thought=None)
    candidate = SimpleNamespace(content=SimpleNamespace(parts=[part]), finish_reason=None)
    return SimpleNamespace(candidates=[candidate], prompt_feedback=None, usage_metadata=None)


def _provider(models):
    return GeminiProvider(
        "clave",
        "gemini-flash-latest",
        light_model="gemini-flash-lite-latest",
        sleep=lambda _: None,
        client=SimpleNamespace(models=models),
    )


def test_call_timeout_never_exceeds_the_time_budget():
    timeouts = []

    class Models:
        def generate_content(self, model, contents, config):
            timeouts.append(config.http_options.timeout)
            return _ok_response()

    _COOLING.clear()
    provider = _provider(Models())
    provider.generate("s", [Message(role="user", text="sin presupuesto")])
    with time_budget(5):
        provider.generate("s", [Message(role="user", text="con presupuesto")])
    assert timeouts[0] == 20_000
    assert 4_000 < timeouts[1] <= 5_000


def test_exhausted_budget_fails_fast_without_cooling_models():
    calls = []

    class Models:
        def generate_content(self, model, contents, config):
            calls.append(model)
            return _ok_response()

    _COOLING.clear()
    provider = _provider(Models())
    with time_budget(0.5), pytest.raises(TimeBudgetExceededError):
        provider.generate("s", [Message(role="user", text="tarde")])
    assert calls == [] and _COOLING == {}
    assert remaining_seconds() is None


def test_slow_model_switches_to_the_other_free_model():
    calls = []

    class Models:
        def generate_content(self, model, contents, config):
            calls.append(model)
            if model == "gemini-flash-latest":
                raise httpx.ReadTimeout("lento")
            return _ok_response()

    _COOLING.clear()
    response = _provider(Models()).generate("s", [Message(role="user", text="hola")])
    assert response.text == "hola"
    assert calls == ["gemini-flash-latest", "gemini-flash-lite-latest"]
    assert "gemini-flash-latest" in _COOLING
    _COOLING.clear()
