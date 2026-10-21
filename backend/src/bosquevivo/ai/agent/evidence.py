import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from bosquevivo.db.models import Evidence


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    kind: str
    reference: str
    payload: dict[str, Any]


class EvidenceStore:
    def __init__(self, session: Session, prefix: str = "ev") -> None:
        self.session = session
        self.prefix = prefix
        self.items: list[EvidenceItem] = []

    def add(self, kind: str, reference: str, payload: dict[str, Any]) -> EvidenceItem:
        body = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
        digest = hashlib.sha256(body.encode()).hexdigest()
        item = EvidenceItem(
            id=f"{self.prefix}_{len(self.items) + 1}_{digest[:8]}",
            kind=kind,
            reference=reference,
            payload=payload,
        )
        self.items.append(item)
        self.session.merge(
            Evidence(
                id=item.id,
                kind=kind,
                reference=reference,
                payload=json.loads(body),
                sha256=digest,
            )
        )
        return item

    def payloads(self) -> list[dict[str, Any]]:
        return [item.payload for item in self.items]

    def ids(self) -> list[str]:
        return [item.id for item in self.items]
