# ADR 0008: Bucle del agente propio y mínimo

- Estado: aceptada

## Decisión
Sin frameworks de agentes. El bucle (`ai/agent/loop.py`) llama al modelo con herramientas tipadas, ejecuta cada llamada con validación Pydantic, acumula evidencias y valida la respuesta final. Máximo de pasos configurable y sin repetir llamadas idénticas.

## Consecuencias
- Comportamiento auditable y fácil de probar con un proveedor guionizado (`ScriptedLLM`).
- Cada paso queda en `agent_run` y `agent_step`.
