# ADR 0009: La IA interpreta, el sistema mide

- Estado: aceptada

## Decisión
Las cifras (índice, hectáreas, porcentajes, fechas) las producen pipelines deterministas. El modelo orquesta herramientas y explica. Un validador (`ai/guardrails/fidelity.py`) comprueba que todo número de la respuesta exista en las evidencias de esa consulta; si no, se reintenta una vez y luego se responde con una plantilla construida con los datos.

## Consecuencias
- Cumple RNF-IA1 (fidelidad numérica) y reduce el riesgo de que una cifra errónea se lea como acusación.
- La visión del modelo describe y evalúa calidad, nunca cuantifica.
