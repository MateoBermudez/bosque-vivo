import hashlib
import json
from pathlib import Path
from typing import Any

from bosquevivo.ai.llm.types import LLMResponse, ToolCall


def request_key(model: str, system: str, payload: list[dict[str, Any]], schema: Any) -> str:
    body = json.dumps(
        {"model": model, "system": system, "payload": payload, "schema": schema},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(body.encode()).hexdigest()


class ResponseCache:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> LLMResponse | None:
        path = self.directory / f"{key}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return LLMResponse(
            text=data["text"],
            tool_calls=[ToolCall(c["name"], c["args"]) for c in data["tool_calls"]],
        )

    def put(self, key: str, response: LLMResponse) -> None:
        if response.blocked:
            return
        data = {
            "text": response.text,
            "tool_calls": [{"name": c.name, "args": c.args} for c in response.tool_calls],
        }
        (self.directory / f"{key}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
