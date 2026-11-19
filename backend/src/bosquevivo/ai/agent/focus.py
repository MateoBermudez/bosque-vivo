from dataclasses import dataclass

from sqlalchemy.orm import Session

from bosquevivo.ai.agent.resolver import Candidate, ProjectResolver

MENTIONED = "mencionado"
CHOSEN = "elegido"
NAME_LIMIT = 70


@dataclass(frozen=True)
class Focus:
    project: tuple[int, str] | None = None
    origin: str | None = None
    clarification: str | None = None
    choices: tuple[tuple[int, str], ...] = ()


def short_name(name: str) -> str:
    return name if len(name) <= NAME_LIMIT else name[: NAME_LIMIT - 3] + "..."


def clarification_text(candidates: tuple[Candidate, ...]) -> str:
    options = "; ".join(f"{i}) {short_name(c.name)}" for i, c in enumerate(candidates, start=1))
    return (
        f"Encontré más de un proyecto que podría ser: {options}. "
        "¿Cuál de ellos es? Puede escribir su nombre completo."
    )


def resolve_focus(session: Session, text: str, chosen: tuple[int, str] | None) -> Focus:
    resolution = ProjectResolver.from_session(session).resolve(text)
    best = resolution.best
    if resolution.confident and best is not None:
        return Focus((best.project_id, best.name), MENTIONED)
    if resolution.candidates:
        return Focus(
            clarification=clarification_text(resolution.candidates),
            choices=tuple((c.project_id, c.name) for c in resolution.candidates),
        )
    if chosen is not None:
        return Focus(chosen, CHOSEN)
    return Focus()
