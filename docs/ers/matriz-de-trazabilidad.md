# Matriz de trazabilidad

| Requisito | Objetivo | Código | Pruebas |
|---|---|---|---|
| RF01 | OE3 | `backend/src/bosquevivo/registry` | `test_registry_import.py`, `test_geometry.py` |
| RF02 | OE3 | `backend/src/bosquevivo/satellite` | `test_satellite_service.py` |
| RF03 | OE3 | `satellite/ndvi.py` | `test_ndvi.py` |
| RF04 | OE3 | `audit/compare.py` | `test_index.py`, `test_audit_service.py` |
| RF05 | OE3 | `audit/index.py`, `audit/components.py`, `audit/confidence.py` | `test_index.py`, `test_golden_projects.py` |
| RF06 | OE3 | `reports` | `test_reports.py` |
| RF07 | OE3 | `assistant`, `api/routers/whatsapp.py` | `test_whatsapp_flow.py`, `test_whatsapp_support.py` |
| RF08 | OE3 | `assistant`, `ai/prompts`, `ai/agent/validation.py` | `test_whatsapp_flow.py`, `test_agent.py` |
| RF09 | Ampliación | `ai/agent` | `test_agent.py`, `test_agent_tools.py` |
| RF10 | Ampliación | `ai/vision`, herramienta `ver_imagenes` | `test_agent_tools.py` |
| RF12 | Ampliación | herramienta `analizar_foto_usuario` | `test_agent_tools.py`, `test_whatsapp_flow.py` |
| RF13 | Ampliación | `assistant/voice.py` | `test_whatsapp_flow.py` |
| RF15 | Ampliación | `ai/knowledge` | `test_knowledge.py` |
| RF17 | Ampliación | `api/routers/chat.py`, `web/src/app/chat`, `web/src/app/api/chat` (antes `panel/pages/3_Chat_del_auditor.py`) | `test_chat_api.py`, `web/src/lib/api/backend.test.ts` |

No implementados en esta etapa: RF11 (modelo propio de visión), RF14 (alertas tempranas) y RF16 (extracción de declaraciones desde PDD). RF09 a RF17 requieren aprobación del docente como revisión del ERS.
