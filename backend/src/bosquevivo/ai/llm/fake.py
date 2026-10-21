from collections.abc import Callable
from typing import Any

from bosquevivo.ai.llm.types import LLMResponse, Message, ToolSpec

Script = list[LLMResponse] | Callable[[str, list[Message], list[ToolSpec] | None], LLMResponse]


class ScriptedLLM:
    def __init__(self, script: Script, model: str = "scripted") -> None:
        self.model = model
        self.script = script
        self.calls: list[dict[str, Any]] = []
        self._cursor = 0

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        json_schema: dict[str, Any] | None = None,
        light: bool = False,
    ) -> LLMResponse:
        self.calls.append(
            {"system": system, "messages": list(messages), "tools": tools, "light": light}
        )
        if callable(self.script):
            return self.script(system, messages, tools)
        if self._cursor >= len(self.script):
            return LLMResponse(text=None, blocked=True)
        response = self.script[self._cursor]
        self._cursor += 1
        return response
