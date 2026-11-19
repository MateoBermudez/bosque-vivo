from bosquevivo.ai.agent.evidence import EvidenceItem

HUMAN_CONTACT = "Si quiere, una persona del equipo puede ayudarle."
BUSY = (
    "En este momento no pude consultar al asistente de inteligencia artificial. Intente de nuevo "
    "en un minuto. Mientras tanto puede preguntarme por un proyecto, por ejemplo «¿Cómo está "
    "Concosta?», y le muestro lo que ya está calculado."
)
UNSURE = (
    "No puedo responder con seguridad a eso porque no tengo datos suficientes para respaldarlo."
)


def _audit_item(items: list[EvidenceItem]) -> EvidenceItem | None:
    for item in reversed(items):
        if item.kind == "auditoria" and item.payload.get("disponible"):
            return item
    return None


def _audit_text(audit: EvidenceItem) -> str:
    p = audit.payload
    if p.get("indice") is None:
        return (
            "Todavía no hay datos suficientes para concluir sobre ese proyecto. "
            "Puede deberse a nubes o a series cortas."
        )
    name = str(p["proyecto"])[:60]
    return (
        f"Según el último cálculo ({p['fecha_calculo']}), {name} tiene una correspondencia "
        f"observada {str(p['categoria']).lower()} ({p['indice']:.0f} de {p['escala_maxima']}) "
        f"con confianza {p['confianza']}. Es lo que se ve desde el satélite, no una acusación."
    )


def _no_data_text(reason: str) -> str:
    return BUSY if reason == "externo" else UNSURE


def fallback_answer(
    items: list[EvidenceItem], role: str, reason: str = "", max_chars: int = 700
) -> str:
    audit = _audit_item(items)
    text = _audit_text(audit) if audit else _no_data_text(reason)
    if role == "comunidad" and len(text) + len(HUMAN_CONTACT) + 1 <= max_chars:
        text = f"{text} {HUMAN_CONTACT}"
    return text
