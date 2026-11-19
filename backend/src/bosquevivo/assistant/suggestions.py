from dataclasses import dataclass

START = "inicio"
CONSENT = "consentimiento"
NO_PROJECT = "sin_proyecto"
WITH_PROJECT = "con_proyecto"

PICK_PROJECT = "elegir_proyecto"
SHARE_LOCATION = "ubicacion"


@dataclass(frozen=True)
class Suggestion:
    label: str
    message: str | None = None
    action: str | None = None


SUGGESTIONS = {
    START: [Suggestion("Empezar", message="Hola")],
    CONSENT: [Suggestion("Acepto el uso de mis datos", message="ACEPTO")],
    NO_PROJECT: [
        Suggestion("Elegir mi proyecto", action=PICK_PROJECT),
        Suggestion("Compartir mi ubicación", action=SHARE_LOCATION),
        Suggestion("¿Qué proyectos hay?", message="¿Qué proyectos hay cargados?"),
    ],
    WITH_PROJECT: [
        Suggestion("¿Cómo está mi bosque?", message="ESTADO"),
        Suggestion("¿Hay alertas?", message="ALERTAS"),
        Suggestion("¿Qué significa mi índice?", message="¿Qué significa el índice de mi proyecto?"),
        Suggestion("Cambiar de proyecto", action=PICK_PROJECT),
    ],
}


CHOICE_LIMIT = 60


def _choice_label(name: str) -> str:
    return name if len(name) <= CHOICE_LIMIT else name[: CHOICE_LIMIT - 3] + "..."


def suggestions_for(stage: str, choices: tuple[tuple[int, str], ...] = ()) -> list[Suggestion]:
    if choices:
        picks = [Suggestion(_choice_label(n), message=f"PROYECTO {pid}") for pid, n in choices]
        return [*picks, Suggestion("Elegir otro proyecto", action=PICK_PROJECT)]
    return list(SUGGESTIONS.get(stage, SUGGESTIONS[START]))
