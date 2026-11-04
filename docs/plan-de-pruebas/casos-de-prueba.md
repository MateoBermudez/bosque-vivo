# Especificación de casos de prueba

Acompaña al [plan de pruebas](plan-de-pruebas.md). Versión 1.2 (04/11/2026): se añaden CP-59 a CP-62 (PostgreSQL en Supabase, migración y despliegue en Vercel). Versión 1.1: CP-53 a CP-58 (correo SMTP, verificación en dos pasos y configuración automática). Cada caso indica el requisito del ERS que verifica, la técnica, las precondiciones, los pasos, los datos, el resultado esperado, la prueba automática que lo ejecuta y el resultado de la ejecución del 03/11/2026.

Rutas de las pruebas: `backend/tests/...` (pytest), `web/src/...` (Vitest) y `docs/plan-de-pruebas/scripts/e2e.cjs` (Playwright, «E2E»).

Estados: **Aprobado**, **Fallido**, **Bloqueado** (depende de credenciales o usuarios externos).

## Resumen

| Requisito | Casos | Aprobados | Bloqueados |
|---|---|---|---|
| RF01 Importar polígonos | CP-01 a CP-06 | 6 | 0 |
| RF02 Series satelitales | CP-07 a CP-09 | 3 | 0 |
| RF03 NDVI | CP-10 a CP-12 | 3 | 0 |
| RF04 Declarado vs observado | CP-13, CP-14 | 2 | 0 |
| RF05 Índice de credibilidad | CP-15 a CP-18 | 4 | 0 |
| RF06 Reporte | CP-19, CP-20 | 2 | 0 |
| RF07 Consultas conversacionales | CP-21 a CP-26 | 6 | 0 |
| RF08 Lenguaje sencillo | CP-27 a CP-29 | 2 | 1 |
| RF09 Recuperación de contraseña | CP-30 a CP-37 | 8 | 0 |
| 3.3.1 Rendimiento | CP-38, CP-39 | 2 | 0 |
| 3.3.2 Seguridad | CP-40 a CP-43 | 4 | 0 |
| 3.3.3 Fiabilidad | CP-44, CP-45 | 2 | 0 |
| 3.3.4 Disponibilidad | CP-46 | 0 | 1 |
| 3.3.5 Mantenibilidad | CP-47 | 1 | 0 |
| 3.3.6 Portabilidad | CP-48 | 1 | 0 |
| Interfaces externas y regresión | CP-49 a CP-52 | 2 | 2 |
| Correo SMTP, 2FA y configuración | CP-53 a CP-58 | 5 | 1 |
| PostgreSQL, migración y despliegue | CP-59 a CP-62 | 4 | 0 |
| **Total** | **62** | **57** | **5** |

## RF01 — Importar polígonos públicos

### CP-01 Importar un GeoJSON válido y la base de Karnik

- **Prioridad:** 3 · **Técnica:** partición de equivalencia (entrada válida)
- **Precondiciones:** base vacía.
- **Pasos:** 1) `bosquevivo import proyectos.geojson --source prueba` o `POST /api/v1/admin/import`. 2) Consultar `GET /api/v1/projects`.
- **Datos:** polígono válido con `project_id`, `project_name`, `country`, `start_year`.
- **Resultado esperado:** confirmación con el identificador interno asignado (`created_ids`); nombre, certificadora, fecha de registro, área y geometría persistidos. En la base de Karnik se conserva el área de contabilidad cuando existe.
- **Automatización:** `integration/test_registry_import.py::test_import_creates_projects`, `integration/test_api.py::test_admin_import`, `integration/test_karnik_import.py::test_conserva_nombre_registro_tipo_y_anio`, `::test_audita_el_area_de_contabilidad_cuando_existe`
- **Resultado:** Aprobado.

### CP-02 Importar un archivo KML

- **Prioridad:** 3 · **Técnica:** partición de equivalencia (formato)
- **Pasos:** importar un KML con `ExtendedData` (`project_id`, `start_year`) en modo estricto.
- **Resultado esperado:** proyecto creado con identificador `VCS-900`, año 2016 y nombre del `Placemark`.
- **Automatización:** `integration/test_strict_import.py::test_kml_import`
- **Resultado:** Aprobado. Ver incidencia INC-01 sobre el formato de atributos admitido.

### CP-03 Rechazar una geometría con auto-intersección

- **Prioridad:** 3 · **Técnica:** valor no válido
- **Datos:** polígono en forma de «corbatín».
- **Resultado esperado:** carga rechazada con el motivo «la geometría no es válida (Self-intersection…)». Con `--lenient` se repara y se cuenta como reparada.
- **Automatización:** `integration/test_strict_import.py::test_strict_rejects_self_intersection`, `::test_lenient_repairs_self_intersection`, `integration/test_karnik_import.py::test_repara_geometrias_invalidas`
- **Resultado:** Aprobado.

### CP-04 Rechazar un identificador duplicado

- **Prioridad:** 3 · **Técnica:** tabla de decisión (existe / no existe)
- **Pasos:** importar dos veces el mismo archivo en modo estricto (CLI y API).
- **Resultado esperado:** la segunda carga crea 0 proyectos, rechaza 1 e informa «el identificador C3 ya existe en el repositorio».
- **Automatización:** `integration/test_strict_import.py::test_strict_rejects_duplicates`, `integration/test_api.py::test_admin_import`
- **Resultado:** Aprobado.

### CP-05 Rechazar filas sin identificador o sin fecha de registro

- **Prioridad:** 3 · **Técnica:** partición de equivalencia (atributos mínimos)
- **Resultado esperado:** rechazo con «falta el identificador del proyecto» o «falta la fecha de registro del proyecto».
- **Automatización:** `integration/test_strict_import.py::test_strict_requires_id_and_date` (2 variantes)
- **Resultado:** Aprobado.

### CP-06 Archivo inexistente o formato no soportado

- **Prioridad:** 3 · **Técnica:** valores no válidos
- **Resultado esperado:** error «no existe el archivo…» o «formato no soportado: .csv (use GeoJSON, KML, GeoPackage o Shapefile)»; archivos que no son de Karnik se rechazan.
- **Automatización:** `integration/test_registry_import.py::test_missing_file_raises`, `integration/test_strict_import.py::test_unsupported_format`, `integration/test_karnik_import.py::test_rechaza_archivos_que_no_son_de_karnik`
- **Resultado:** Aprobado.

## RF02 — Obtener series satelitales históricas

### CP-07 Serie desde la fecha de certificación hasta hoy

- **Prioridad:** 3
- **Precondiciones:** proyecto con T0 conocido.
- **Resultado esperado:** observaciones mensuales guardadas por sensor; Sentinel-2 no se pide antes de su ventana de operación; la ventana empieza 3 años antes de T0; recálculo reemplaza las observaciones previas.
- **Automatización:** `integration/test_satellite_service.py::test_refresh_timeseries_stores_months`, `::test_sentinel2_not_requested_before_launch_window`, `::test_refresh_replaces_previous_observations`, `integration/test_karnik_import.py::test_t0_sale_de_la_fecha_completa_de_inicio`
- **Resultado:** Aprobado. Con datos reales (proveedor `open`) ver CP-39.

### CP-08 Umbral de nubosidad configurable (20 % por defecto)

- **Prioridad:** 3 · **Técnica:** valores límite (0–100)
- **Resultado esperado:** `CLOUD_MAX_PERCENT` vale 20 por defecto, acepta 35 y rechaza 150; el valor usado queda en la trazabilidad (`dataset_versions.cloud_max_percent`) y filtra `CLOUDY_PIXEL_PERCENTAGE` (Sentinel-2) y `CLOUD_COVER` (Landsat).
- **Automatización:** `unit/test_gee_support.py::test_umbral_de_nubes_por_defecto_es_20_y_se_valida`, `::test_el_umbral_de_nubes_queda_en_la_trazabilidad`
- **Resultado:** Aprobado.

### CP-09 Sin escenas suficientes

- **Prioridad:** 2
- **Resultado esperado:** se registra un incidente «series_satelitales» de origen externo y severidad «aviso», y el índice sale «Insuficiente» con confianza baja en lugar de un valor.
- **Automatización:** `integration/test_incidents.py::test_missing_scenes_create_incident`, `unit/test_index.py::test_no_valid_data_is_insufficient`, `golden/test_golden_projects.py::test_insufficient_project_has_no_score_and_low_confidence`
- **Resultado:** Aprobado.

## RF03 — Calcular el NDVI

### CP-10 Fórmula del NDVI

- **Prioridad:** 1 · **Técnica:** valores conocidos
- **Datos:** NIR = 0,5, Rojo = 0,1 → 0,6667; NIR = Rojo → 0; NIR = Rojo = 0 → sin dato.
- **Automatización:** `unit/test_ndvi.py::test_ndvi_basic_values`
- **Resultado:** Aprobado.

### CP-11 Descartar NDVI fuera de [−1, 1]

- **Prioridad:** 1 · **Técnica:** valores límite
- **Resultado esperado:** píxeles fuera de rango quedan sin dato; puntos con media fuera de rango no se guardan y se registran como escena inválida.
- **Automatización:** `unit/test_ndvi.py::test_ndvi_out_of_range_is_discarded`, `::test_invalid_points_are_detected`, `integration/test_incidents.py::test_out_of_range_points_are_discarded`
- **Resultado:** Aprobado (corrige INC-06).

### CP-12 Compuesto mensual y promedio zonal

- **Prioridad:** 1
- **Resultado esperado:** las escenas de un mes se resumen con la mediana; una escena totalmente enmascarada cuenta como sin dato.
- **Automatización:** `unit/test_ndvi.py::test_monthly_composite_groups_scenes_and_uses_median`, `::test_fully_masked_scene_counts_as_no_data`
- **Resultado:** Aprobado.

## RF04 — Comparar cobertura declarada y observada

### CP-13 Alineación temporal con T0

- **Prioridad:** 1
- **Resultado esperado:** los años posteriores a T0 se marcan para la comparación; la pérdida anterior a T0 no penaliza; la fecha declarada revisada reemplaza la del registro; una declaración no revisada se ignora.
- **Automatización:** `unit/test_index.py::test_comparison_marks_years_after_t0`, `::test_loss_before_t0_is_ignored`, `integration/test_audit_service.py::test_declared_t0_overrides_registry_year`, `::test_unreviewed_declaration_is_ignored`
- **Resultado:** Aprobado.

### CP-14 Caídas significativas y umbrales configurables

- **Prioridad:** 1 · **Técnica:** valores límite
- **Resultado esperado:** una caída abrupta del NDVI reduce la estabilidad; la pérdida posterior a T0 reduce la permanencia; los umbrales viven en `IndexConfig` y los pesos deben sumar 1.
- **Automatización:** `unit/test_index.py::test_abrupt_ndvi_drop_lowers_stability_and_trend_is_flat`, `::test_loss_after_t0_lowers_permanence`, `::test_weights_must_sum_to_one`, `integration/test_audit_service.py::test_forest_loss_and_ndvi_drop_reduce_score`
- **Resultado:** Aprobado.

## RF05 — Calcular el índice de credibilidad

### CP-15 Escala de 0 a 1

- **Prioridad:** 1
- **Resultado esperado:** el índice se muestra como «0,82» además de 82/100 en el sitio y en el reporte.
- **Automatización:** `web/src/lib/format.test.ts` («índice en escala de 0 a 1»), `integration/test_reports.py`
- **Resultado:** Aprobado.

### CP-16 Categorías alta, media, baja e insuficiente

- **Prioridad:** 1 · **Técnica:** valores límite (75 y 50)
- **Resultado esperado:** bosque intacto → alta; con pérdida → menor; sin datos → «Insuficiente»; v1 distingue proyectos que v0 deja en 100.
- **Automatización:** `unit/test_index.py::test_intact_forest_scores_high`, `unit/test_index_v1.py` (13 pruebas), `golden/test_golden_projects.py::test_expected_category`, `::test_intact_scores_higher_than_damaged`
- **Resultado:** Aprobado.

### CP-17 Proyectos golden

- **Prioridad:** 1
- **Resultado esperado:** tres polígonos de referencia obtienen la categoría esperada.
- **Automatización:** `golden/test_golden_projects.py`
- **Resultado:** Aprobado.

### CP-18 Reproducibilidad de los insumos

- **Prioridad:** 1
- **Resultado esperado:** cada corrida guarda parámetros, versión del índice, versión del código (`git_sha`) y conjuntos de datos; el rango de sensibilidad acota el puntaje.
- **Automatización:** `integration/test_audit_service.py::test_audit_run_persists_result_and_traceability`, `unit/test_index.py::test_sensitivity_range_brackets_score`
- **Resultado:** Aprobado.

## RF06 — Generar el reporte de auditoría

### CP-19 Contenido del reporte HTML y PDF

- **Prioridad:** 3
- **Resultado esperado:** incluye polígono, serie NDVI, comparación, índice (0–100 y 0–1), confianza, fuentes satelitales, fecha de generación y limitaciones; escapa el nombre del proyecto; no usa lenguaje acusatorio; el PDF es válido.
- **Automatización:** `integration/test_reports.py` (5 pruebas)
- **Resultado:** Aprobado.

### CP-20 Descarga desde el sitio

- **Prioridad:** 3
- **Resultado esperado:** `/informe/[runId]` entrega el archivo con su tipo de contenido o 404 si no existe.
- **Automatización:** `web/src/lib/api/backend.test.ts` («devuelve el reporte con su tipo de contenido, o null si no existe»)
- **Resultado:** Aprobado.

## RF07 — Recibir consultas conversacionales

### CP-21 Primer contacto

- **Prioridad:** 2
- **Pasos:** escribir «Hola» por WhatsApp o en el chat en línea.
- **Resultado esperado:** saludo que aclara que es una IA y aviso de privacidad que pide ACEPTO; no se llama al modelo.
- **Automatización:** `integration/test_whatsapp_flow.py::test_first_contact_sends_welcome_and_notice_without_calling_model`, `integration/test_community_chat.py::test_web_chat_follows_consent_and_intents`, E2E CP-21
- **Resultado:** Aprobado.

### CP-22 Sin autorización no se responde

- **Prioridad:** 2 · **Técnica:** tabla de decisión (consentimiento)
- **Resultado esperado:** antes de ACEPTO cualquier consulta recibe «Escriba ACEPTO para continuar»; el consentimiento queda registrado con la versión del aviso.
- **Automatización:** `integration/test_whatsapp_flow.py::test_questions_before_consent_are_not_answered`, `::test_consent_is_logged_with_notice_version`, E2E CP-22
- **Resultado:** Aprobado.

### CP-23 Intención «ayuda»

- **Prioridad:** 2
- **Resultado esperado:** AYUDA (o «menú») lista ESTADO, ALERTAS, PROYECTO y BORRAR MIS DATOS sin llamar al modelo.
- **Automatización:** `integration/test_whatsapp_intents.py::test_help_without_model`, `::test_detect_intent`, E2E CP-23
- **Resultado:** Aprobado.

### CP-24 Registro del polígono de interés

- **Prioridad:** 2 · **Técnica:** partición de equivalencia (número válido / inexistente / ubicación)
- **Resultado esperado:** «PROYECTO 1» registra el proyecto; un número inexistente responde «No encontré ese número»; una ubicación dentro de un polígono lo asocia.
- **Automatización:** `integration/test_whatsapp_intents.py::test_register_then_status_and_alerts`, `::test_location_registers_project`, E2E CP-24
- **Resultado:** Aprobado.

### CP-25 Intención «alertas»

- **Prioridad:** 2 · **Técnica:** valores límite (0,5 % del bosque por año)
- **Resultado esperado:** sin proyecto registrado pide registrarlo; con pérdida ≥ 0,5 % anual en los últimos 3 años informa año, hectáreas y porcentaje; sin pérdida informa «Sin alertas».
- **Automatización:** `integration/test_whatsapp_intents.py::test_alerts_require_project`, `::test_alert_thresholds`, `::test_alerts_without_loss_records`, E2E CP-25
- **Resultado:** Aprobado (corrige INC-04).

### CP-26 Intención no reconocida

- **Prioridad:** 2
- **Resultado esperado:** si la consulta no se reconoce y el agente no tiene datos, se responde con la ayuda en lugar de fallar en silencio, también sin clave de IA.
- **Automatización:** `integration/test_whatsapp_intents.py::test_unknown_question_without_model_gets_help`, `integration/test_community_chat.py::test_works_without_gemini_key`, E2E CP-26
- **Resultado:** Aprobado (corrige INC-07).

## RF08 — Responder en lenguaje sencillo

### CP-27 Estado del bosque en términos de cobertura

- **Prioridad:** 2
- **Resultado esperado:** «En Reserva El Roble se conserva el 100 % del bosque que había desde 2018. En general, lo que se ve desde el satélite coincide bien con lo que el proyecto declara.»
- **Automatización:** `integration/test_whatsapp_intents.py::test_register_then_status_and_alerts`, E2E CP-27
- **Resultado:** Aprobado.

### CP-28 Sin jerga, sin acusaciones y mensajes cortos

- **Prioridad:** 2
- **Resultado esperado:** ningún mensaje supera 300 caracteres; no aparecen «fraude», «NDVI», «REDD» ni «índice» en las respuestas a la comunidad; el agente bloquea lenguaje acusatorio.
- **Automatización:** `integration/test_whatsapp_intents.py::test_register_then_status_and_alerts`, `integration/test_whatsapp_flow.py::test_answer_after_consent_respects_length`, `unit/test_guardrails.py::test_accusatory_terms_are_detected`, `integration/test_agent.py::test_accusatory_language_is_blocked`, `::test_community_answer_longer_than_limit_falls_back`, E2E CP-28
- **Resultado:** Aprobado.

### CP-29 Comprensión con usuarios no técnicos

- **Prioridad:** 2 · **Técnica:** prueba de usabilidad
- **Pasos:** 5 personas sin formación técnica usan el asistente con un guion de 5 tareas (saludo, aceptar, registrar proyecto, estado, alertas) y explican con sus palabras lo que entendieron.
- **Resultado esperado:** al menos 4 de 5 personas interpretan correctamente el estado y las alertas.
- **Resultado:** Bloqueado (requiere el piloto con usuarios).

## RF09 — Recuperación de contraseña

### CP-30 Acceso restringido

- **Prioridad:** 2
- **Resultado esperado:** `/chat` y `/trazas` redirigen a `/acceso`; la API del chat responde 401 sin sesión.
- **Automatización:** `web/src/lib/auth/access.test.ts`, E2E CP-30
- **Resultado:** Aprobado.

### CP-31 Credenciales inválidas y bloqueo

- **Prioridad:** 2 · **Técnica:** valores límite (5 intentos, 10 minutos)
- **Resultado esperado:** «El correo o la contraseña no son correctos.»; tras 5 fallos la cuenta se bloquea 10 minutos y luego se libera.
- **Automatización:** `integration/test_password_recovery.py::test_authenticate_and_lock_after_failures`, `::test_login_endpoint`, `web/src/lib/auth/throttle.test.ts`, E2E CP-31
- **Resultado:** Aprobado.

### CP-32 Mensaje genérico

- **Prioridad:** 2 · **Técnica:** partición (correo registrado / no registrado / inactivo)
- **Resultado esperado:** el mismo texto «Si la dirección está registrada, recibirás un correo…» en los tres casos; solo se envía correo a cuentas activas.
- **Automatización:** `integration/test_password_recovery.py::test_unknown_email_gets_same_message_and_no_mail`, `::test_reset_endpoints_full_flow`, `::test_disabled_user_cannot_login_or_reset`, E2E CP-32
- **Resultado:** Aprobado.

### CP-33 Correo con enlace seguro de un solo uso

- **Prioridad:** 2
- **Resultado esperado:** el correo contiene `WEB_BASE_URL/acceso/restablecer?token=…` y el vencimiento (30 minutos); el token se guarda solo como SHA-256; una nueva solicitud invalida la anterior; máximo 3 solicitudes por hora; SMTP con STARTTLS y autenticación.
- **Automatización:** `integration/test_password_recovery.py::test_reset_flow_sends_single_use_link`, `::test_token_is_stored_hashed`, `::test_new_request_invalidates_previous_token`, `::test_reset_requests_are_throttled`, `::test_smtp_mailer_uses_tls_and_login`, `::test_outbox_mailer_writes_eml`, E2E CP-33
- **Resultado:** Aprobado.

### CP-34 Token inválido, vencido o usado

- **Prioridad:** 2 · **Técnica:** valores límite (minuto 31)
- **Resultado esperado:** «El enlace no es válido», «El enlace venció» o «El enlace ya se usó», con la invitación a solicitar uno nuevo (HTTP 410).
- **Automatización:** `integration/test_password_recovery.py::test_token_expires`, `::test_invalid_token_and_weak_password`, `::test_reset_endpoints_full_flow`, `web/src/lib/api/accounts.test.ts`, E2E CP-34
- **Resultado:** Aprobado.

### CP-35 Validación de la contraseña nueva

- **Prioridad:** 2 · **Técnica:** partición de equivalencia
- **Datos:** contraseñas distintas, menos de 10 caracteres, sin número, sin letra, igual al correo.
- **Resultado esperado:** rechazo con el motivo; el token sigue válido.
- **Automatización:** `integration/test_password_recovery.py::test_password_policy`, `::test_invalid_token_and_weak_password`, `web/src/lib/auth/throttle.test.ts`, E2E CP-35
- **Resultado:** Aprobado.

### CP-36 Actualización y confirmación

- **Prioridad:** 2
- **Resultado esperado:** «Tu contraseña se actualizó. Ya puedes iniciar sesión.»; la contraseña anterior deja de funcionar.
- **Automatización:** `integration/test_password_recovery.py::test_reset_flow_sends_single_use_link`, E2E CP-36
- **Resultado:** Aprobado.

### CP-37 Inicio de sesión con la contraseña nueva

- **Prioridad:** 2
- **Resultado esperado:** se entra a `/trazas`; la sesión es una cookie firmada que guarda el correo y no puede alterarse.
- **Automatización:** `web/src/lib/auth/session.test.ts`, E2E CP-37
- **Resultado:** Aprobado.

## Requisitos no funcionales

### CP-38 Tiempo de respuesta del asistente (3.3.1)

- **Meta:** ≥ 90 % de las consultas en menos de 10 s.
- **Pasos:** `uv run bosquevivo medir-rnf --rounds 100`.
- **Resultado obtenido:** 100 % bajo 10 s (p90 = 0,005 s) en las intenciones del ERS; con Gemini real se repite en el piloto.
- **Automatización:** `integration/test_measure.py`; evidencia `evidencias/rnf-fake.json`, `rnf-open.json`.
- **Resultado:** Aprobado.

### CP-39 Tiempo de cálculo del índice por polígono (3.3.1)

- **Meta:** < 5 min por polígono.
- **Resultado obtenido:** con datos abiertos reales (MODIS 250 m + Hansen) 43,7 s, 44,7 s y 62,9 s en los tres polígonos de demostración (máximo 62,9 s).
- **Evidencia:** `evidencias/rnf-open.json`
- **Resultado:** Aprobado. Repetir con `SATELLITE_PROVIDER=gee` cuando haya cuenta de Earth Engine.

### CP-40 Firma del webhook y token de administración (3.3.2)

- **Resultado esperado:** un POST sin firma `X-Hub-Signature-256` válida responde 401; la verificación del webhook solo devuelve el desafío con el token correcto; las rutas de administración, autenticación, chat y chat comunitario exigen `X-Admin-Token`.
- **Automatización:** `integration/test_whatsapp_flow.py::test_webhook_rejects_bad_signature`, `::test_webhook_verification_handshake`, `unit/test_whatsapp_support.py::test_tampered_body_or_missing_header_is_rejected`, `integration/test_password_recovery.py::test_auth_endpoints_require_admin_token`, `integration/test_community_chat.py::test_requires_admin_token`, `integration/test_api.py::test_request_audit_requires_admin_token`
- **Resultado:** Aprobado.

### CP-41 Teléfono como HMAC y números autorizados (3.3.2, RF07)

- **Resultado esperado:** el número nunca se guarda en claro; con `WHATSAPP_ALLOWED_PHONES` solo se atiende a los números listados y no se crea registro de los demás.
- **Automatización:** `integration/test_whatsapp_flow.py::test_phone_is_stored_only_as_hmac`, `unit/test_privacy.py`, `integration/test_whatsapp_intents.py::test_allowlist`, `::test_unauthorized_phone_is_not_stored`
- **Resultado:** Aprobado.

### CP-42 Supresión de datos (Ley 1581)

- **Resultado esperado:** BORRAR MIS DATOS elimina el usuario, los consentimientos, las consultas y la evidencia asociada.
- **Automatización:** `integration/test_whatsapp_flow.py::test_delete_command_removes_user_consents_and_traces`, `::test_delete_command_also_removes_evidence_of_the_user_queries`, `integration/test_community_chat.py::test_web_chat_follows_consent_and_intents`, E2E CP-42
- **Resultado:** Aprobado.

### CP-43 Credenciales protegidas

- **Resultado esperado:** contraseñas con scrypt y sal (dos hashes de la misma clave difieren); tokens de recuperación como SHA-256; secretos solo en `.env` (ignorado por git); el agente bloquea la fuga de secretos.
- **Automatización:** `integration/test_password_recovery.py::test_password_hash_roundtrip_and_salt`, `::test_token_is_stored_hashed`, `integration/test_agent.py::test_secret_leak_in_answer_is_blocked`; revisión de `.gitignore`.
- **Resultado:** Aprobado.

### CP-44 Determinismo (3.3.3)

- **Resultado esperado:** con los mismos insumos y parámetros el índice es idéntico.
- **Resultado obtenido:** 3 de 3 proyectos con el mismo índice en dos cálculos (97,2/97,2; 96,0/96,0; 56,1/56,1 con datos abiertos).
- **Automatización:** `integration/test_measure.py::test_measure_audits_and_determinism`; evidencia `rnf-open.json`.
- **Resultado:** Aprobado.

### CP-45 Registro de incidentes (3.3.3, 3.3.5)

- **Resultado esperado:** cada incidente guarda componente, origen (externo/interno), severidad, inicio, fin y duración; más de 60 min se marca crítico; los fallos de tareas, del modelo y del correo se registran; `bosquevivo incidents` los resume.
- **Automatización:** `integration/test_incidents.py` (5 pruebas), `integration/test_password_recovery.py::test_mail_failure_is_recorded_as_external_incident`
- **Resultado:** Aprobado.

### CP-46 Disponibilidad del 95 % en el horario del piloto (3.3.4)

- **Pasos:** durante el horario acordado, `scripts/disponibilidad.sh http://127.0.0.1:8000/health <minutos>`; al final `bosquevivo incidents`.
- **Resultado esperado:** ≥ 95 % de minutos con `/health` en 200 y ≤ 2 incidentes críticos al mes.
- **Resultado:** Bloqueado (se mide en el piloto).

### CP-47 Parámetros como configuración (3.3.5)

- **Resultado esperado:** umbral de nubosidad, umbrales de caída del NDVI, pesos y categorías del índice, vencimiento del token y lista de números se cambian por configuración, sin tocar el código.
- **Automatización:** `unit/test_gee_support.py::test_umbral_de_nubes_por_defecto_es_20_y_se_valida`, `unit/test_index_v1.py::test_version_desconocida_se_rechaza`, `integration/test_password_recovery.py::test_token_expires`
- **Resultado:** Aprobado.

### CP-48 Portabilidad (3.3.6)

- **Resultado esperado:** el sistema se instala y ejecuta con herramientas abiertas en un entorno local (Linux en CI y en esta ejecución; Windows con `scripts/dev.ps1`); la migración ligera actualiza bases existentes.
- **Automatización:** CI de GitHub Actions; `integration/test_whatsapp_intents.py::test_upgrade_adds_missing_column`; `integration/test_lifespan.py`
- **Resultado:** Aprobado.

## Interfaces externas y regresión

### CP-49 WhatsApp Cloud API real

- **Pasos:** seguir [`docs/guias/whatsapp.md`](../guias/whatsapp.md) y repetir CP-21 a CP-28 desde un teléfono de prueba.
- **Resultado:** Bloqueado (requiere credenciales de Meta del dueño).

### CP-50 Evaluación del agente con Gemini real

- **Pasos:** `uv run bosquevivo eval --output data/eval/report.json` (20 casos: herramientas, fidelidad, neutralidad, incertidumbre, fugas, longitud y latencia).
- **Resultado:** Bloqueado (requiere `GEMINI_API_KEY`). El arnés se prueba con un modelo guionizado: `eval/test_eval_harness.py`.

### CP-51 Regresión del agente de IA (RA01–RA09)

- **Resultado esperado:** uso de herramientas, corrección de cifras inventadas, respaldo ante cuota agotada, separación de herramientas por rol, inyección de instrucciones, límite de pasos y límite diario.
- **Automatización:** `integration/test_agent.py` (16 pruebas), `integration/test_agent_tools.py`, `integration/test_knowledge.py`, `integration/test_chat_api.py`, `unit/test_guardrails.py`
- **Resultado:** Aprobado.

### CP-52 Regresión del sitio y del panel

- **Resultado esperado:** `eslint`, `tsc`, 94 pruebas de Vitest, `next build` y 5 pruebas del panel sin errores.
- **Evidencia:** `evidencias/web-vitest.txt`, `web-junit.xml`, `web-lint.txt`, `web-build.txt`
- **Resultado:** Aprobado.

## Correo SMTP, verificación en dos pasos y configuración

### CP-53 Verificación en dos pasos por correo

- **Requisito:** RF09 y 3.3.2 (seguridad del panel web) · **Prioridad:** 2
- **Precondiciones:** cuenta activa; SMTP configurado (o `AUTH_TWO_FACTOR=on`).
- **Pasos:** iniciar sesión con correo y contraseña correctos; leer el correo; escribir el código.
- **Resultado esperado:** tras la contraseña se pide un código de 6 dígitos enviado al correo (mostrado enmascarado, «au*****@elpoli.edu.co»); con el código correcto se entra. Una contraseña incorrecta no envía código. Con `AUTH_TWO_FACTOR=auto` se activa solo cuando hay SMTP.
- **Automatización:** `integration/test_two_factor.py::test_login_sends_code_and_verifies`, `::test_wrong_password_does_not_send_code`, `::test_two_factor_can_be_disabled`, `::test_auto_two_factor_follows_smtp`, `::test_two_factor_endpoints`, `web/src/lib/api/accounts.test.ts`, E2E CP-53
- **Resultado:** Aprobado.

### CP-54 Código incorrecto, vencido, reutilizado y reenvío

- **Prioridad:** 2 · **Técnica:** valores límite (5 intentos, 10 minutos, 3 envíos)
- **Resultado esperado:** código incorrecto → «El código no es correcto.»; al quinto fallo, al vencer o al reutilizarse, la verificación se anula y hay que iniciar sesión de nuevo; «Reenviar código» envía uno nuevo e invalida el anterior, hasta 3 envíos.
- **Automatización:** `integration/test_two_factor.py::test_wrong_code_counts_attempts_until_exhausted`, `::test_code_expires_and_is_single_use`, `::test_resend_replaces_code_with_limit`, E2E CP-54
- **Resultado:** Aprobado.

### CP-55 Avisos de seguridad por correo

- **Prioridad:** 2
- **Resultado esperado:** correo de nuevo inicio de sesión (fecha en hora de Colombia, navegador, sistema e IP), de contraseña cambiada y de cuenta bloqueada; todos con versión de texto y HTML. Una falla de envío de un aviso no impide la operación y queda como incidente externo.
- **Automatización:** `integration/test_two_factor.py::test_lock_sends_security_email`, `::test_password_change_notifies`, `::test_message_has_text_and_html`, `integration/test_password_recovery.py::test_mail_failure_is_recorded_as_external_incident`, E2E CP-55
- **Resultado:** Aprobado.

### CP-56 Invitación de cuentas

- **Prioridad:** 2
- **Pasos:** `bosquevivo user-invite correo --name Nombre`; abrir el enlace del correo; elegir contraseña.
- **Resultado esperado:** la cuenta se crea sin contraseña utilizable; el correo trae un enlace de un solo uso válido 72 horas; la página da la bienvenida y, al guardar, se puede iniciar sesión. No se envía el aviso de «contraseña cambió».
- **Automatización:** `integration/test_two_factor.py::test_invitation_sets_first_password`, `::test_verify_reports_purpose`, E2E CP-56
- **Resultado:** Aprobado (corrige INC-12).

### CP-57 Configuración SMTP

- **Prioridad:** 3
- **Resultado esperado:** con solo `SMTP_USER` y `SMTP_PASSWORD` se detecta el servidor (Gmail, Google Workspace, Outlook, Yahoo); `MAIL_BACKEND=auto` usa SMTP si hay credenciales y el buzón local si no; STARTTLS en 587 y SSL en 465; un error transitorio se reintenta; un error de autenticación explica que se use una contraseña de aplicación; `bosquevivo mail-test` verifica la configuración.
- **Automatización:** `integration/test_two_factor.py::test_smtp_presets_and_auto_backend`, `::test_smtp_retries_and_explains_auth_errors`, `integration/test_password_recovery.py::test_smtp_mailer_uses_tls_and_login`, `::test_build_mailer_validates_configuration`
- **Resultado:** Aprobado. El envío por un servidor SMTP real se ejecuta en el piloto con `bosquevivo mail-test` (Bloqueado hasta tener las credenciales).

### CP-58 Configuración automática

- **Requisito:** 3.3.5 y 3.3.6 · **Prioridad:** 3
- **Pasos:** en un clon nuevo, `scripts/dev.sh` (o `scripts\dev.ps1`).
- **Resultado esperado:** `bosquevivo setup` crea `backend/.env` y `web/.env.local`, genera `ADMIN_TOKEN`, `PHONE_HMAC_KEY`, `WHATSAPP_VERIFY_TOKEN` y `SESSION_SECRET`, elige datos abiertos si no hay Earth Engine, crea la base con 3 proyectos de demostración, conserva comentarios y valores existentes al repetirse, y lista solo las claves externas que faltan.
- **Automatización:** `integration/test_setup.py` (4 pruebas); prueba manual de `scripts/start.sh` en modo producción (API, sitio y chat en línea respondiendo).
- **Resultado:** Aprobado.

## PostgreSQL, migración y despliegue

### CP-59 Suite completa contra PostgreSQL

- **Requisito:** 3.3.6 Portabilidad, 3.3.3 Fiabilidad · **Prioridad:** 2
- **Pasos:** `TEST_DATABASE_URL=postgresql://… uv run pytest` sobre un PostgreSQL 16 vacío.
- **Resultado esperado:** las mismas pruebas que con SQLite pasan con PostgreSQL (tipos con zona horaria, largo de columnas, migración ligera, secuencias).
- **Resultado obtenido:** 330 de 330 aprobadas en PostgreSQL 16; la CI ejecuta las dos variantes en cada cambio.
- **Resultado:** Aprobado.

### CP-60 Conexión a Supabase por el pooler

- **Prioridad:** 2
- **Resultado esperado:** `DATABASE_URL` con `[YOUR-PASSWORD]` se completa con `DATABASE_PASSWORD` codificada; `postgres://` y `postgresql://` usan el controlador psycopg; los hosts remotos exigen `sslmode=require`; en funciones sin estado se usa `NullPool` y sin sentencias preparadas (compatible con el *Transaction pooler*); la contraseña no aparece en los registros.
- **Automatización:** `unit/test_database_urls.py` (5 pruebas)
- **Resultado:** Aprobado. Verificado contra Supabase en producción (pooler `aws-0-us-east-1`).

### CP-61 Migración de SQLite a PostgreSQL

- **Prioridad:** 2
- **Pasos:** `uv run bosquevivo migrate-db --from sqlite:///… --to postgresql://…`
- **Resultado esperado:** copia las 21 tablas en orden de dependencias, informa los valores que superan el largo de su columna antes de copiar, se niega a sobrescribir sin `--replace`, reinicia las secuencias y verifica los conteos; después se pueden crear registros nuevos.
- **Resultado obtenido:** 233 filas en 21 tablas copiadas a PostgreSQL 16; luego se crearon un usuario (id 3) y una auditoría (corrida 4) sin conflictos de identificador.
- **Automatización:** `integration/test_migrate.py` (2 pruebas)
- **Resultado:** Aprobado.

### CP-62 API liviana y despliegue en Vercel

- **Prioridad:** 2
- **Pasos:** instalar solo el núcleo de dependencias, arrancar la API con `VERCEL=1` contra PostgreSQL y recorrer salud, proyectos, reportes, chat comunitario y solicitud de auditoría; luego `VERCEL_TOKEN=… scripts/deploy-vercel.sh`.
- **Resultado esperado:** el núcleo pesa menos de 500 MB; la API arranca sin las librerías de cálculo; las tareas se procesan en la misma petición; los reportes PDF y HTML se generan al vuelo; una auditoría pedida a la API desplegada falla con el mensaje de usar la CLI.
- **Resultado obtenido:** núcleo de 274 MB; API en modo Vercel respondió `/health`, proyectos, reporte PDF (200) y HTML (200), chat comunitario y la auditoría quedó «failed» con el mensaje esperado. `integration/test_inline_jobs.py` (4 pruebas).
- **Despliegue real (04/11/2026):** API en https://bosque-vivo-api.vercel.app y sitio en https://bosque-vivo-web.vercel.app sobre Supabase. Se detectó y corrigió una colisión al crear el esquema con varias instancias a la vez (INC-15). `push-db` subió 7.163 filas en 6 s; `/api/v1/projects` devolvió 58 proyectos; reporte PDF 200 en 1,1 s; chat en línea respondió el saludo y el aviso; `/proyectos` pasó de 15–25 s a 1–2 s con el endpoint `/api/v1/explorer` (INC-16).
- **Resultado:** Aprobado.

