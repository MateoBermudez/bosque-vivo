# Plan de pruebas (OE4)

## Ejecución
```
cd backend
uv run pytest            # unitarias, integración, golden y arnés de evaluación
uv run pytest -m golden  # solo polígonos de validación
uv run bosquevivo eval   # evaluación del agente con Gemini real (requiere clave)
```

## Capas
| Capa | Ubicación | Qué cubre |
|---|---|---|
| Unitarias | `backend/tests/unit` | NDVI, geometrías, índice, guardas, WhatsApp, límites del modelo, CLI |
| Integración | `backend/tests/integration` | SQLite en memoria, proveedor de satélite simulado, API, agente con modelo guionizado, flujo de WhatsApp |
| Golden | `backend/tests/golden` | Tres polígonos con categoría esperada |
| Evaluación de IA | `backend/tests/eval` y `bosquevivo.ai.eval` | 20 casos: herramientas, fidelidad, neutralidad, incertidumbre, fugas, longitud, latencia |
| Panel | `panel/tests` | Transformaciones de datos del panel |

## Matriz RF → pruebas

| Requisito | Pruebas |
|---|---|
| RF01 Importar polígonos | `integration/test_registry_import.py`, `unit/test_geometry.py` |
| RF02 Series satelitales | `integration/test_satellite_service.py` |
| RF03 NDVI | `unit/test_ndvi.py` |
| RF04 Declarado vs observado | `unit/test_index.py::test_comparison_marks_years_after_t0`, `integration/test_audit_service.py` |
| RF05 Índice | `unit/test_index.py`, `golden/test_golden_projects.py`, `integration/test_audit_service.py` |
| RF06 Reporte | `integration/test_reports.py` |
| RF07 Recibir consultas | `unit/test_whatsapp_support.py`, `integration/test_whatsapp_flow.py` (firma, idempotencia, cola) |
| RF08 Lenguaje sencillo | `integration/test_whatsapp_flow.py::test_answer_after_consent_respects_length`, `integration/test_agent.py` (límite de 300 caracteres) |
| RF09 Agente con herramientas | `integration/test_agent.py`, `integration/test_agent_tools.py` |
| RF10 Análisis visual | `integration/test_agent_tools.py::test_images_tool_*` |
| RF12 Fotos | `integration/test_agent_tools.py::test_user_photo_*`, `integration/test_whatsapp_flow.py::test_photo_requires_separate_consent` |
| RF13 Voz | `integration/test_whatsapp_flow.py::test_audio_*` |
| RF15 Base de conocimiento | `integration/test_knowledge.py` |
| RF17 Chat del auditor | `integration/test_chat_api.py` |
| RNF-IA1 Fidelidad numérica | `unit/test_guardrails.py`, `integration/test_agent.py::test_invented_number_*` |
| RNF-IA2 Incertidumbre | `unit/test_index.py` (Insuficiente), `integration/test_agent.py::test_fallback_when_no_audit_*` |
| RNF-IA3 Trazabilidad | `integration/test_agent.py::test_trace_is_persisted` |
| RNF-IA4 Neutralidad | `unit/test_guardrails.py`, `integration/test_agent.py::test_accusatory_language_is_blocked`, `integration/test_reports.py` |
| RNF-IA6 Seguridad | `integration/test_agent.py` (inyección, fuga de secretos, roles, topes) |
| Ley 1581 | `integration/test_whatsapp_flow.py` (consentimiento, HMAC, borrado) |

## Requisitos no funcionales: cómo se medirán

Estado: **pendiente de medición**. Se medirá en la instancia local durante la semana 7.

| NFR del ERS | Medición |
|---|---|
| 90 % de consultas en < 10 s | Script con ≥ 100 consultas rápidas; p50 y p90 incluyendo la llamada al modelo. `bosquevivo eval` ya reporta latencia por caso |
| Índice en ≤ 5 min por polígono | Benchmark con polígonos pequeños, medianos y grandes sobre Earth Engine; `audit_run.duration_seconds` guarda la duración |
| 95 % de disponibilidad en el piloto | Consulta de `/health` cada minuto durante el horario del piloto |
| ≤ 2 incidentes críticos al mes | Bitácora de incidentes |
| TLS 1.2+ | Verificación del túnel con `testssl.sh` o SSL Labs sobre la URL pública |

## Resultados
Se registran en `docs/testing/resultados.md` después de cada ejecución completa.
