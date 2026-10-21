from bosquevivo.audit.index import INSUFFICIENT, IndexOutcome


def build_narrative(outcome: IndexOutcome, project_name: str) -> str:
    confidence = outcome.confidence.label
    if outcome.category == INSUFFICIENT or outcome.score is None:
        permanence = next((c for c in outcome.components if c.name == "permanencia"), None)
        if permanence and permanence.score is None and "motivo" in permanence.detail:
            return (
                f"En {project_name} no se pudo calcular la permanencia del bosque porque no hay "
                f"bosque de referencia al inicio del periodo (año 2000) dentro de su polígono. "
                f"Es lo esperado en proyectos de reforestación, que el índice v0 todavía no "
                f"cubre; no indica un problema del proyecto."
            )
        return (
            f"No hay datos suficientes para estimar la correspondencia observada en "
            f"{project_name}. La confianza es {confidence}; es habitual con nubosidad alta "
            f"o series cortas."
        )
    parts = [
        f"La correspondencia observada para {project_name} es {outcome.category.lower()} "
        f"({outcome.score:.0f} de 100), con confianza {confidence}."
    ]
    permanence = next((c for c in outcome.components if c.name == "permanencia"), None)
    if permanence and permanence.score is not None:
        parts.append(
            f"Se observa en pie el {permanence.detail['porcentaje_en_pie']} % del bosque "
            f"inicial desde la fecha de acreditación."
        )
    parts.append(
        "Es una descripción de lo que se ve desde el satélite, no una conclusión sobre "
        "intenciones de nadie."
    )
    return " ".join(parts)
