from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    name: str
    content: dict[str, Any]


@dataclass(frozen=True)
class MediaPart:
    data: bytes
    mime_type: str


@dataclass
class Message:
    role: Literal["user", "model", "tool"]
    text: str | None = None
    media: list[MediaPart] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    raw: Any = None


@dataclass
class LLMResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None
    blocked: bool = False
    prompt_tokens: int = 0
    output_tokens: int = 0
