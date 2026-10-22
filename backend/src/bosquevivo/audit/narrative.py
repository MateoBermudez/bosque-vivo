from bosquevivo.audit.index import INSUFFICIENT, IndexOutcome


def build_narrative(outcome: IndexOutcome, project_name: str) -> str:
    confidence = outcome.confidence.label
    if outcome.category == INSUFFICIENT or outcome.score is None:
        permanence = next((c for c in outcome.components if c.name == "permanencia"), None)
        if permanence and permanence.score is not None and outcome.confidence.value == 0.0:
            return (
                f"Para {project_name} solo se pudo medir la permanencia del bosque: se observa en "
                f"pie el {permanence.detail['porcentaje_en_pie']} % del bosque inicial desde la "
                f"fecha de acreditación, según el mapa de pérdida de Hansen. Faltan datos "
                f"utilizables de verdor (NDVI) para calcular la tendencia y la estabilidad, por "
                f"eso todavía no hay un puntaje del índice. Es una descripción de lo que se ve "
                f"desde el satélite, no una conclusión sobre intenciones de nadie."
            )
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
    evolution = next((c for c in outcome.components if c.name == "evolucion_perdida"), None)
    if evolution and evolution.score is not None and "cociente_despues_antes" in evolution.detail:
        parts.append(
            f"La pérdida anual de bosque pasó de {evolution.detail['perdida_anual_antes_ha']} ha "
            f"antes de la acreditación a {evolution.detail['perdida_anual_despues_ha']} ha después "
            f"(x{evolution.detail['cociente_despues_antes']}); es una comparación del propio "
            f"polígono, que no descarta causas regionales."
        )
    parts.append(
        "Es una descripción de lo que se ve desde el satélite, no una conclusión sobre "
        "intenciones de nadie."
    )
    return " ".join(parts)
