from typing import Any, Protocol

from bosquevivo.ai.llm.types import LLMResponse, Message, ToolSpec


class LLMProvider(Protocol):
    model: str

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        json_schema: dict[str, Any] | None = None,
        light: bool = False,
    ) -> LLMResponse: ...
