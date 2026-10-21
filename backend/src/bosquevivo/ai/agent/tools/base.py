from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from bosquevivo.ai.agent.evidence import EvidenceStore
from bosquevivo.ai.llm import LLMProvider, MediaPart, ToolSpec
from bosquevivo.core.config import Settings
from bosquevivo.satellite.service import SatelliteService

Role = Literal["comunidad", "auditor"]


class ToolError(Exception):
    pass


@dataclass
class ToolContext:
    session: Session
    settings: Settings
    evidence: EvidenceStore
    role: Role
    llm: LLMProvider | None = None
    satellite: SatelliteService | None = None
    location: tuple[float, float] | None = None
    user_media: list[MediaPart] = field(default_factory=list)
    media_consent: bool = False


@dataclass
class ToolOutput:
    content: dict[str, Any]
    media: list[MediaPart] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)


Handler = Callable[[ToolContext, Any], ToolOutput]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]
    handler: Handler
    roles: tuple[Role, ...] = ("comunidad", "auditor")


def clean_schema(schema: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "title":
            continue
        if isinstance(value, dict):
            cleaned[key] = clean_schema(value)
        elif isinstance(value, list):
            cleaned[key] = [clean_schema(v) if isinstance(v, dict) else v for v in value]
        else:
            cleaned[key] = value
    return cleaned


class ToolRegistry:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {t.name: t for t in tools}

    def names(self, role: Role) -> list[str]:
        return [name for name, tool in self._tools.items() if role in tool.roles]

    def specs(self, role: Role) -> list[ToolSpec]:
        return [
            ToolSpec(
                name=t.name,
                description=t.description,
                parameters=clean_schema(t.args_model.model_json_schema()),
            )
            for t in self._tools.values()
            if role in t.roles
        ]

    def call(self, name: str, args: dict[str, Any], ctx: ToolContext) -> ToolOutput:
        tool = self._tools.get(name)
        if tool is None or ctx.role not in tool.roles:
            raise ToolError(f"herramienta no disponible: {name}")
        try:
            parsed = tool.args_model(**args)
        except ValidationError as exc:
            raise ToolError(f"argumentos inválidos para {name}: {exc.errors()[0]['msg']}") from exc
        return tool.handler(ctx, parsed)
