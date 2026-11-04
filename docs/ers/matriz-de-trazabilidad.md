# Matriz de trazabilidad

Requisitos del ERS (IEEE 830, versión del 20/10/2026 en el Drive del proyecto) y de la ampliación con IA. Los casos de prueba (CP-xx) están en [`docs/plan-de-pruebas/casos-de-prueba.md`](../plan-de-pruebas/casos-de-prueba.md).

## Requisitos funcionales del ERS

| Requisito | Objetivo | Código | Pruebas automáticas | Casos |
|---|---|---|---|---|
| RF01 Importar polígonos | OE3 | `registry/importer.py` (GeoJSON, KML, GeoPackage; modo estricto), `registry/karnik.py`, `api/routers/admin.py` | `test_registry_import.py`, `test_strict_import.py`, `test_karnik_import.py`, `test_geometry.py` | CP-01 a CP-06 |
| RF02 Series satelitales | OE3 | `satellite/service.py`, `satellite/providers/*` (`CLOUD_MAX_PERCENT`) | `test_satellite_service.py`, `test_opendata_provider.py`, `test_hansen_provider.py`, `test_incidents.py` | CP-07 a CP-09 |
| RF03 NDVI | OE3 | `satellite/ndvi.py` | `test_ndvi.py`, `test_incidents.py` | CP-10 a CP-12 |
| RF04 Declarado vs observado | OE3 | `audit/compare.py`, `audit/components.py` | `test_index.py`, `test_audit_service.py` | CP-13, CP-14 |
| RF05 Índice de credibilidad | OE3 | `audit/index.py`, `audit/confidence.py`, `audit/config.py` | `test_index.py`, `test_index_v1.py`, `test_golden_projects.py`, `format.test.ts` | CP-15 a CP-18 |
| RF06 Reporte de auditoría | OE3 | `reports/*`, `web/src/app/informe` | `test_reports.py` | CP-19, CP-20 |
| RF07 Consultas conversacionales | OE3 | `assistant/*`, `api/routers/whatsapp.py`, `api/routers/community.py` | `test_whatsapp_flow.py`, `test_whatsapp_support.py`, `test_whatsapp_intents.py`, `test_community_chat.py` | CP-21 a CP-26 |
| RF08 Lenguaje sencillo | OE3 | `assistant/community.py`, `assistant/texts.py`, `ai/prompts`, `ai/guardrails` | `test_whatsapp_intents.py`, `test_guardrails.py`, `test_agent.py` | CP-27 a CP-29 |
| RF09 Recuperación de contraseña | OE3 | `accounts/*` (correo SMTP, verificación en dos pasos, avisos, invitaciones), `api/routers/auth.py`, `web/src/app/acceso/*` | `test_password_recovery.py`, `test_two_factor.py`, `session.test.ts`, `access.test.ts`, `accounts.test.ts`, `throttle.test.ts` | CP-30 a CP-37, CP-53 a CP-57 |

## Requisitos no funcionales del ERS

| Requisito | Cómo se cumple | Verificación |
|---|---|---|
| 3.3.1 Rendimiento | `AgentRun.latency_ms`, `AuditRun.duration_seconds` | `scripts/medir_rnf.py` (CP-38, CP-39) |
| 3.3.2 Seguridad | HMAC del teléfono, firma del webhook, scrypt, tokens SHA-256, verificación en dos pasos por correo, avisos de seguridad, secretos en `.env` generados por `bosquevivo setup` | CP-40 a CP-43, CP-53 a CP-55 |
| 3.3.3 Fiabilidad | Registro de incidentes (`core/incidents.py`, `bosquevivo incidents`), cálculos deterministas | CP-44, CP-45 |
| 3.3.4 Disponibilidad | Medición en el horario del piloto | CP-46 (pendiente del piloto) |
| 3.3.5 Mantenibilidad | Parámetros en configuración, origen externo/interno en los registros, configuración automática | CP-47, CP-58 |
| 3.3.6 Portabilidad | Código abierto, ejecución local en Windows/Linux (`scripts/dev`, `scripts/start`) | CP-48, CP-58 |

## Ampliación con IA (pendiente de aprobación del docente)

Antes se numeraba RF09–RF17; se renombró RA01–RA09 porque el ERS usa RF09 para la recuperación de contraseña.

| Requisito | Antes | Código | Pruebas |
|---|---|---|---|
| RA01 Agente multi-paso | RF09 | `ai/agent` | `test_agent.py`, `test_agent_tools.py` |
| RA02 Análisis visual | RF10 | `ai/vision`, herramienta `ver_imagenes` | `test_agent_tools.py` |
| RA04 Fotos y ubicación del usuario | RF12 | herramienta `analizar_foto_usuario` | `test_agent_tools.py`, `test_whatsapp_flow.py` |
| RA05 Notas de voz | RF13 | `assistant/voice.py` | `test_whatsapp_flow.py` |
| RA07 Base de conocimiento | RF15 | `ai/knowledge` | `test_knowledge.py` |
| RA09 Chat del auditor | RF17 | `api/routers/chat.py`, `web/src/app/chat`, `web/src/app/api/chat` | `test_chat_api.py`, `backend.test.ts` |

No implementados (evolución prevista, sección 2.6 del ERS): RA03 (modelo propio de visión), RA06 (alertas tempranas en tiempo casi real) y RA08 (extracción de declaraciones desde PDD).
