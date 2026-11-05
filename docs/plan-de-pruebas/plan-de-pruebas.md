---
title: "Plan de Pruebas de Software"
subtitle: "Bosque Vivo"
date: "03/11/2026"
lang: es-CO
---

# Plan de Pruebas de Software

**Proyecto:** Bosque Vivo — Sistema de información para la auditoría de la supervivencia forestal posterior a la certificación de proyectos de carbono

**Fecha:** 03/11/2026

Estructura: plantilla «Formato_ieee829» del Politécnico Colombiano Jaime Isaza Cadavid, basada en IEEE Std 829. Este documento cubre el objetivo específico 4 del proyecto (probar el sistema mediante un plan de pruebas que verifique el cumplimiento de los requerimientos) y se apoya en la Especificación de Requisitos de Software (ERS, IEEE 830), revisión 1.1 del 05/11/2026; los requisitos RF01–RF09 y los no funcionales son los mismos de la versión del 20/10/2026.

Documentos que lo acompañan:

| Documento | Contenido |
|---|---|
| [`casos-de-prueba.md`](casos-de-prueba.md) | Especificación de los 62 casos de prueba (CP-01 a CP-62) |
| [`informe-de-resultados.md`](informe-de-resultados.md) | Ejecución, métricas, mediciones de requisitos no funcionales y evaluación de los criterios de aceptación |
| [`incidencias.md`](incidencias.md) | Registro de incidencias encontradas durante la ejecución |
| [`evidencias/`](evidencias) | Salidas de las herramientas, reportes JUnit, cobertura, mediciones y capturas |
| [`scripts/`](scripts) | Scripts de prueba de extremo a extremo y de disponibilidad |

## 1. Historial de Versiones

| Fecha | Versión | Autor | Descripción |
|---|---|---|---|
| 20/10/2026 | 0.1 | Equipo Bosque Vivo | Primer plan (`docs/testing/plan-de-pruebas.md`): capas de prueba y matriz RF → pruebas, sin el formato IEEE 829 |
| 03/11/2026 | 1.0 | Equipo Bosque Vivo | Plan completo según la plantilla IEEE 829, alineado con el ERS del 20/10/2026 (RF01–RF09 y requisitos no funcionales), casos de prueba, ejecución y resultados |
| 03/11/2026 | 1.1 | Equipo Bosque Vivo | Correo SMTP con verificación en dos pasos, avisos de seguridad e invitaciones; configuración automática; casos CP-53 a CP-58 |
| 04/11/2026 | 1.2 | Equipo Bosque Vivo | PostgreSQL en Supabase, migración desde SQLite y despliegue en Vercel; casos CP-59 a CP-62 |
| 05/11/2026 | 1.3 | Equipo Bosque Vivo | Referencia a la revisión 1.1 del ERS (correcciones de edición e interfaces de IA, correo, datos abiertos y alojamiento; requisitos sin cambios) |
|  |  |  |  |

## 2. Información del Proyecto

| Campo | Valor |
|---|---|
| Empresa / Organización | Politécnico Colombiano Jaime Isaza Cadavid — Ingeniería Informática, Proyecto Integrador (ODS 15) |
| Proyecto | Bosque Vivo |
| Representante de Equipo | Mateo Bermúdez Cuartas |

## 3. Aprobaciones

| Nombre y Apellido | Cargo | Departamento u Organización | Fecha | Firma |
|---|---|---|---|---|
| Mateo Bermúdez Cuartas | Desarrollador, representante del equipo | Politécnico Colombiano Jaime Isaza Cadavid |  |  |
| Emmanuel Arango Velásquez | Desarrollador | Politécnico Colombiano Jaime Isaza Cadavid |  |  |
| Miguel Ángel Calle Parra | Desarrollador | Politécnico Colombiano Jaime Isaza Cadavid |  |  |
| Miguel Ángel Agudelo Tamayo | Desarrollador | Politécnico Colombiano Jaime Isaza Cadavid |  |  |
| Juan David Andrade Vanegas | Desarrollador | Politécnico Colombiano Jaime Isaza Cadavid |  |  |
| (Docente evaluador) | Docente del Proyecto Integrador | Politécnico Colombiano Jaime Isaza Cadavid |  |  |

## 4. Alcance y Estrategia de las Pruebas

El objeto de prueba es la versión de Bosque Vivo de la rama `main` del repositorio `MateoBermudez/bosque-vivo` a 03/11/2026: la API y los módulos de dominio (`backend/`), el sitio web (`web/`) y el panel Streamlit en desuso (`panel/`). Se prueban los dos sistemas de información del ERS —Verificación y Auditoría, y Asistente Conversacional— más el panel web de solo lectura con su administración de cuentas (RF09).

### 4.1 Elementos de Pruebas

| Módulo / componente | Ubicación | Requisitos | Qué se prueba |
|---|---|---|---|
| Importación de polígonos | `backend/src/bosquevivo/registry` | RF01 | Carga de GeoJSON, KML y GeoPackage; validación geométrica (auto-intersecciones); identificador y fecha de registro obligatorios; rechazo de duplicados con motivo; persistencia y metadatos (área de contabilidad de Karnik et al., 2025) |
| Series satelitales | `backend/src/bosquevivo/satellite` | RF02 | Consulta por polígono y rango desde la fecha de certificación; filtro de nubosidad configurable (20 % por defecto); registro de incidencia cuando no hay escenas |
| Cálculo del NDVI | `satellite/ndvi.py` | RF03 | Fórmula (NIR − Rojo)/(NIR + Rojo); descarte de valores fuera de [−1, 1]; compuesto mensual y promedio zonal |
| Comparación declarado–observado | `audit/compare.py`, `audit/components.py` | RF04 | Alineación temporal con la fecha T0; umbrales de caída configurables; clasificación |
| Índice de credibilidad | `audit/index.py`, `audit/confidence.py`, `audit/config.py` | RF05 | Escala 0–1 (y 0–100); categorías alta/media/baja e «Insuficiente»; confianza; reproducibilidad de los insumos |
| Reportes | `backend/src/bosquevivo/reports`, `web/src/app/informe` | RF06 | Reporte HTML y PDF con polígono, serie NDVI, comparación, índice, fuentes y fecha; descarga desde el sitio |
| Asistente conversacional | `backend/src/bosquevivo/assistant`, `api/routers/whatsapp.py`, `api/routers/community.py`, `web/src/app/asistente` | RF07, RF08 | Webhook firmado; consentimiento (Ley 1581); intenciones estado, alertas y ayuda; registro del polígono de interés; números autorizados; respuestas en español sencillo y de longitud acotada; chat en línea como canal alterno |
| Cuentas y recuperación de contraseña | `backend/src/bosquevivo/accounts`, `api/routers/auth.py`, `web/src/app/acceso` | RF09 | Inicio de sesión; mensaje genérico; token de un solo uso con vencimiento; validación de la contraseña nueva; confirmación; bloqueo por intentos; invitaciones |
| Correo SMTP y verificación en dos pasos | `accounts/mailer.py`, `accounts/templates.py`, `accounts/service.py` | RF09, 3.3.2 | Código de 6 dígitos por correo (intentos, vencimiento, reenvío); avisos de inicio de sesión, cambio de contraseña y bloqueo; detección del servidor SMTP, TLS, reintentos; buzón local sin SMTP |
| Configuración automática | `bosquevivo/setup.py`, `scripts/dev.*`, `scripts/start.*` | 3.3.5, 3.3.6 | Generación de secretos y `.env`, base y datos de demostración, lista de claves externas pendientes, modo producción |
| Base de datos y despliegue | `db/session.py`, `db/urls.py`, `db/migrate.py`, `jobs/dispatch.py`, `backend/index.py`, `scripts/deploy-vercel.sh` | 3.3.3, 3.3.6 | Suite completa en PostgreSQL, conexión por el pooler de Supabase, migración desde SQLite, API liviana en modo Vercel |
| Agente de IA (ampliación) | `backend/src/bosquevivo/ai` | RA01–RA09 | Herramientas, validador de fidelidad, neutralidad, inyección de instrucciones, respaldo determinista (regresión con modelo guionizado) |
| Incidentes y mediciones | `core/incidents.py`, `measure.py` | 3.3.1, 3.3.3, 3.3.5 | Registro de incidentes con origen externo/interno y duración; tiempos de respuesta y de cálculo; determinismo |
| Sitio web | `web/` | 3.1.1 | Contrato de la API (zod), sesión firmada, componentes de dominio, compilación de producción |

### 4.2 Pruebas de Regresión

Funcionalidades que no son el foco de los cambios de esta versión pero comparten componentes con ellos y se vuelven a probar en cada ejecución:

| Funcionalidad (vista del usuario) | Por qué se afecta | Qué se verifica cada vez |
|---|---|---|
| Consultar el mapa y el detalle de un proyecto | Usa la misma API y base de datos que la importación estricta | Listado, polígono aligerado, serie y última auditoría (`test_api.py`, `test_karnik_import.py`, `backend.test.ts`) |
| Calcular una auditoría en lote | Comparte el servicio satelital, ahora con descarte de NDVI y registro de incidentes | `test_pipeline_batch.py`, `test_audit_service.py`, `test_golden_projects.py` |
| Conversación con WhatsApp (consentimiento, fotos, voz, borrado) | El flujo del asistente se reorganizó para las nuevas intenciones y la lista de números | `test_whatsapp_flow.py` completo |
| Chat del auditor y trazas | Comparte el agente y la sesión del área de auditores, que ahora usa cuentas | `test_chat_api.py`, `access.test.ts`, `session.test.ts`, E2E CP-37 |
| Agente de IA | Ahora registra incidentes cuando el modelo falla | `test_agent.py`, `test_agent_tools.py`, `test_eval_harness.py` |
| Reportes | Se añadió la escala 0–1 | `test_reports.py` |
| Panel Streamlit (en desuso) | Consume la misma API | `panel/tests` |

Aspectos que se revisan en cada regresión: (1) toda la suite automática pasa (`pytest`, `vitest`, `ruff`, `pyright`, `eslint`, `tsc`, `next build`); (2) la cobertura del backend no baja de 80 %; (3) el lenguaje del producto sigue siendo neutro (nunca «fraude»); (4) ningún secreto queda en el repositorio. La integración continua de GitHub Actions (`.github/workflows/ci.yml`) ejecuta la regresión en cada solicitud de cambio.

### 4.3 Elementos a No Probar

| Elemento | Razón | Riesgo asumido |
|---|---|---|
| Google Earth Engine real (`SATELLITE_PROVIDER=gee`) | Requiere una cuenta y un proyecto de Earth Engine del dueño; no está disponible en el entorno de pruebas | Los tiempos de cálculo con Earth Engine pueden superar los medidos con datos abiertos. Mitigación: el cálculo se probó con el proveedor de datos abiertos real (MODIS + Hansen) y la lógica de Earth Engine se aísla tras `SatelliteProvider`. Queda como CP-39 en ejecución complementaria |
| Envío real por WhatsApp Cloud API | Requiere credenciales de Meta del dueño ([guía](../guias/whatsapp.md)) | Diferencias del formato real del webhook. Mitigación: el webhook se prueba con cargas reales de la documentación de Meta, firma HMAC y el mismo flujo por el chat en línea. Queda como CP-49 |
| Respuestas de Gemini real y evaluación del agente | Requiere `GEMINI_API_KEY` ([guía](../guias/gemini.md)) | Calidad de las respuestas libres no medida. Mitigación: modelo guionizado, validador de fidelidad, respuesta de respaldo y las intenciones del ERS funcionan sin IA. Queda como CP-50 |
| Envío SMTP real de correos | Requiere una cuenta de correo del dueño ([guía](../guias/correo.md)) | Bloqueo del proveedor de correo. Mitigación: el remitente SMTP (TLS, autenticación, reintentos) se prueba con un servidor simulado y el flujo completo —invitación, 2FA, avisos y recuperación— con el buzón local `.eml` y `AUTH_TWO_FACTOR=on`. Se verifica en el piloto con `bosquevivo mail-test` (CP-57) |
| Disponibilidad 95 % y ≤ 2 incidentes críticos al mes | Solo se puede medir durante el piloto, en el horario que se acuerde con el docente | Se entrega el script `scripts/disponibilidad.sh` y el comando `bosquevivo incidents`. Queda como CP-46 |
| Comprensión con 5 personas no técnicas | Requiere usuarios reales | Mensajes poco claros. Mitigación: textos breves, revisados contra la lista de jerga. Queda como CP-29 |
| RA03, RA06 y RA08 (modelo propio de visión, alertas en tiempo casi real, extracción de PDD) | Fuera del alcance de esta entrega (sección 2.6 del ERS) | Ninguno para el alcance comprometido |
| Rendimiento con miles de usuarios concurrentes | El ERS define un prototipo en modo sandbox, no un servicio en producción | No aplica |

### 4.4 Enfoque de Pruebas (Estrategia)

**Tipos de prueba.**

- Funcionales: cada requisito RF01–RF09 tiene casos positivos y negativos (casos-de-prueba.md).
- De interfaces: contratos HTTP de la API (FastAPI `TestClient`), contrato backend–sitio validado con zod, webhook de WhatsApp con firma.
- No funcionales: rendimiento (comando `bosquevivo medir-rnf`), seguridad (firmas, HMAC, scrypt, tokens, secretos), fiabilidad (determinismo, incidentes), mantenibilidad (configuración), portabilidad (ejecución local y CI en Linux).
- De extremo a extremo: navegador Chromium con Playwright sobre la API y el sitio reales (`scripts/ejecutar-e2e.sh`).
- De regresión: suite completa automática en cada cambio.
- De aceptación con usuarios: piloto (pendiente).

**Cuadrantes de pruebas ágiles (Marick, Crispin y Gregory).**

| Cuadrante | Propósito | En Bosque Vivo |
|---|---|---|
| Q1 — tecnología, apoyo al equipo | Pruebas unitarias y de componentes, automatizadas | 108 pruebas unitarias (NDVI, índice, guardas, contraseñas, firma, privacidad) y pruebas de componentes del sitio |
| Q2 — negocio, apoyo al equipo | Pruebas funcionales y de ejemplos, automatizadas | 179 pruebas de integración por requisito, 5 «golden» con categoría esperada, 20 verificaciones E2E |
| Q3 — negocio, crítica al producto | Exploratorias, usabilidad, aceptación | Revisión visual de pantallas (capturas), prueba de comprensión y piloto (pendientes con usuarios) |
| Q4 — tecnología, crítica al producto | Rendimiento, seguridad, fiabilidad | `medir-rnf`, determinismo, incidentes, análisis estático (`ruff`, `pyright`, `eslint`) |

**Pirámide de automatización.** La base son las pruebas unitarias (rápidas, sin red), luego las de integración con SQLite en memoria y proveedores simulados (satélite `fake`, modelo guionizado, correo en memoria), y en la punta unas pocas pruebas E2E en navegador. Las dependencias externas (Earth Engine, Gemini, Meta, SMTP) están detrás de interfaces (`SatelliteProvider`, `LLMProvider`, `WhatsAppClient`, `Mailer`) para poder sustituirlas en las pruebas.

**Proceso.** (1) Se especifica el caso a partir del requisito del ERS. (2) Se automatiza en la capa más baja posible. (3) Se ejecuta la suite completa localmente y en CI. (4) Cada falla se registra como incidencia con severidad, se corrige y se vuelve a ejecutar la suite. (5) Los resultados y evidencias se guardan en `evidencias/`.

**Prioridad.**

| Prioridad | Módulos | Motivo |
|---|---|---|
| 1 | RF05 índice, RF04 comparación, RF03 NDVI | Núcleo de la pregunta de investigación; un error invalida las conclusiones |
| 2 | RF07, RF08 asistente; RF09 cuentas, verificación en dos pasos y avisos; seguridad y Ley 1581 | Datos personales y canal principal de la comunidad |
| 3 | RF01 importación, RF02 series, RF06 reporte | Entrada y salida del flujo de auditoría |
| 4 | Rendimiento, fiabilidad, portabilidad | Metas a validar durante el piloto |
| 5 | Ampliación de IA (RA) | Pendiente de aprobación del docente |

### 4.5 Criterios de Aceptación

#### 4.5.1 Criterios de Aceptación

Criterios para dar por completado el plan:

1. 100 % de las pruebas automáticas aprobadas (backend, sitio y panel) y análisis estático sin errores.
2. Cobertura de líneas del backend ≥ 80 %.
3. 100 % de los requisitos funcionales RF01–RF09 con al menos un caso ejecutado y aprobado.
4. 100 % de los casos de prioridad 1 y 2 ejecutados.
5. 0 incidencias abiertas de severidad crítica o alta.
6. Rendimiento: ≥ 90 % de las consultas del asistente en menos de 10 s y cálculo del índice en menos de 5 min por polígono.
7. Determinismo: mismo índice con los mismos insumos.
8. La compilación de producción del sitio termina sin errores.

Criterios del usuario para aceptar el aplicativo (ERS): el auditor puede consultar el índice, la serie y el reporte de un proyecto; la comunidad recibe respuestas cortas en español sencillo; los datos personales se tratan según la Ley 1581; y el resultado se presenta como análisis metodológico, sin atribuir fraude.

Los casos o partes que dependen de credenciales o usuarios externos (CP-29, CP-46, CP-49, CP-50 y el envío SMTP real de CP-57) se registran como «Bloqueado» y no impiden cerrar el plan; se ejecutan en el piloto.

### 4.6 Entregables

- Este plan de pruebas (Markdown, `.docx` y `.pdf`).
- Especificación de casos de prueba (`casos-de-prueba.md`).
- Informe de resultados con métricas y evaluación de criterios (`informe-de-resultados.md`).
- Registro de incidencias (`incidencias.md`).
- Evidencias: reportes JUnit (`backend-junit.xml`, `web-junit.xml`), salidas de `pytest` con cobertura, `vitest`, `ruff`, `pyright`, `eslint`, `next build`, mediciones de requisitos no funcionales (`rnf-fake.json`, `rnf-open.json`), resultado E2E (`e2e-resultados.json`, `e2e-salida.txt`) y capturas de pantalla.
- Scripts reutilizables: `scripts/ejecutar-e2e.sh`, `scripts/e2e.cjs`, `scripts/disponibilidad.sh` y los comandos `bosquevivo medir-rnf`, `bosquevivo mail-test` y `bosquevivo setup`.

## 5. Recursos

### 5.1 Requerimientos de Entornos – Hardware

| Recurso | Especificación |
|---|---|
| Equipo de prueba | Computador personal con Windows 11 o Linux, 8 GB de RAM o más, 5 GB libres en disco (el ERS y el ADR 0002 definen ejecución local, sin servidores ni máquinas virtuales) |
| Red | Conexión a Internet estable para las fuentes de datos abiertos (Hansen en Google Cloud Storage, MODIS en Planetary Computer) y, en el piloto, para WhatsApp, Gemini y el túnel HTTPS |
| Usuario final | Cualquier teléfono con WhatsApp o un navegador web |
| Integración continua | Máquinas `ubuntu-latest` de GitHub Actions |

### 5.2 Requerimientos de Entornos – Software

| Software | Versión | Uso |
|---|---|---|
| Python | 3.12 | Backend y panel |
| uv | 0.5 o superior | Entornos y dependencias de Python |
| Node.js | 22 o superior (CI con 24) | Sitio web |
| Base de datos | SQLite (incluida en Python) y PostgreSQL 16 | Base de pruebas en memoria, bases temporales y la misma suite contra PostgreSQL (`TEST_DATABASE_URL`, servicio de la CI); producción en Supabase |
| Chromium + Playwright | Versión preinstalada | Pruebas de extremo a extremo |
| Git y GitHub | — | Control de versiones y CI |
| Accesos (piloto) | — | Clave de Google AI Studio, app de Meta para WhatsApp, cuenta de Earth Engine, cuenta de correo SMTP |

Datos de prueba: tres proyectos de demostración (`bosquevivo seed-demo`), polígonos sintéticos dentro de las pruebas, cargas de webhook de la documentación de Meta y los 55 polígonos reales de Karnik et al. (2025) para Colombia.

### 5.3 Herramientas de Pruebas Requeridas

| Herramienta | Uso |
|---|---|
| pytest, pytest-cov | Pruebas unitarias, de integración, golden y del arnés de evaluación; cobertura |
| FastAPI TestClient | Pruebas de la API sin levantar servidor |
| Vitest | Pruebas del sitio (contrato zod, cliente del backend, sesión, formato) |
| Playwright (Chromium) | Pruebas E2E en navegador |
| Ruff, Pyright | Estilo y tipos del backend |
| ESLint, TypeScript (`tsc`), `next build` | Calidad y compilación del sitio |
| `bosquevivo medir-rnf` | Tiempos de respuesta, tiempos de cálculo y determinismo |
| `bosquevivo incidents` | Bitácora de incidentes (origen, duración, criticidad) |
| `bosquevivo eval` | Evaluación del agente con Gemini real (20 casos) |
| `scripts/disponibilidad.sh` | Disponibilidad del servicio durante el piloto |
| GitHub Actions | Regresión automática en cada cambio |
| Técnicas | Partición de equivalencia y valores límite (NDVI en [−1, 1], umbrales del índice, vencimiento del token, intentos fallidos), tablas de decisión (consentimiento y registro del asistente), pruebas basadas en riesgo y casos «golden» |

### 5.4 Entrenamiento

| Tema | Quién | Material |
|---|---|---|
| Ejecutar la suite y leer la cobertura | Todo el equipo | `README.md` (sección Calidad) y este plan |
| Proveedores simulados y modelo guionizado | Quien escriba pruebas nuevas | `backend/tests/conftest.py`, `ai/llm/fake.py`, `satellite/providers/fake.py` |
| Playwright para E2E | Responsable de la interfaz | `scripts/e2e.cjs` |
| Configurar WhatsApp, Gemini y correo para el piloto | Representante del equipo | [`docs/guias`](../guias) |
| Lenguaje neutro y Ley 1581 | Todo el equipo | `docs/privacy/aviso-de-privacidad.md`, ADR 0009 |

## 6. Planificación y Organización

### 6.1 Matriz de Responsabilidades

Propuesta de reparto; el equipo puede ajustarla antes de firmar.

| Integrante | Responsabilidades en las pruebas |
|---|---|
| Mateo Bermúdez Cuartas | Líder de pruebas: plan, integración continua, ejecución completa, RF09 (cuentas, contraseña, verificación en dos pasos y correo SMTP), E2E, registro de incidencias y configuración del piloto (WhatsApp, Gemini, correo) |
| Emmanuel Arango Velásquez | Sitio web: pruebas de Vitest, revisión visual de pantallas, accesibilidad, chat en línea y descarga de reportes (RF06 en el sitio) |
| Miguel Ángel Calle Parra | Datos geoespaciales: RF01 (importación), RF02 (series) y RF03 (NDVI); ejecución con Earth Engine real (CP-39) |
| Miguel Ángel Agudelo Tamayo | Analítica: RF04 (comparación), RF05 (índice y casos golden), RF06 (reportes); determinismo (CP-44) |
| Juan David Andrade Vanegas | Asistente: RF07 y RF08, prueba de comprensión con usuarios (CP-29), mediciones de rendimiento y disponibilidad en el piloto (CP-38, CP-46) |

### 6.2 Cronograma

| Actividad | Fecha |
|---|---|
| Plan inicial y suite automática base | 20/10/2026 |
| Implementación de RF09 y cierre de brechas del ERS | 03/11/2026 |
| Especificación de casos, ejecución completa, E2E y mediciones | 03/11/2026 |
| Configuración de credenciales (WhatsApp, Gemini, correo) | Semana del piloto |
| Piloto: CP-29, CP-46, CP-49, CP-50 | Horario acordado con el docente |
| Cierre y firmas | Entrega final del semestre |

## 7. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación / contingencia |
|---|---|---|---|
| Cuotas de la capa gratuita de Gemini agotadas durante la evaluación | Media | Medio | Límites propios por minuto, día y usuario; respuesta de respaldo determinista; las intenciones del ERS no usan IA |
| Cambio de precios de WhatsApp Cloud API | Media | Medio | El piloto queda dentro de los 1.000 mensajes de servicio gratuitos al mes; el chat en línea `/asistente` reemplaza a WhatsApp sin costo |
| Sin acceso a Earth Engine | Media | Medio | Proveedor de datos abiertos (MODIS + Hansen) probado con datos reales |
| Nubosidad persistente que deja proyectos sin escenas | Alta | Medio | Se registra la incidencia y el índice sale «Insuficiente» con confianza baja, en lugar de un valor |
| Dependencias de desarrollo pendientes (credenciales del dueño) | Alta | Bajo | Casos marcados «Bloqueado» con guía paso a paso para ejecutarlos |
| Disponibilidad del equipo (semestre académico) | Media | Medio | Suite automatizada en CI; reparto por módulos |
| Restricciones de tiempo | Media | Medio | Priorización por riesgo (sección 4.4) |
| Premisa falsa: el polígono publicado no es el área de los créditos | Baja | Alto | Se usa el área de contabilidad de Karnik et al. cuando existe y se documenta |
| Pruebas frágiles por dependencias externas | Media | Bajo | Interfaces con dobles de prueba; las pruebas no usan red |

## 8. Referencias

| Referencia | Documento |
|---|---|
| Plan de Proyecto | `docs/planning/PLAN_IMPLEMENTACION.md`, `docs/planning/PLAN_AGENTE_IA.md` |
| Especificación de Requerimientos | ERS «Formato_ieee830», revisión 1.1 del 05/11/2026 (`docs/ers/ERS_Bosque_Vivo.docx` y `.pdf`); `docs/ers/matriz-de-trazabilidad.md` |
| Diseño General | `docs/architecture/arquitectura.md` |
| Diseño Detallado | `docs/architecture/adr/0001` a `0013`; `docs/methodology/indice-v0.md` e `indice-v1.md` |
| Procedimientos y estándares de Desarrollo | `README.md` (reglas del repositorio), `.pre-commit-config.yaml`, `.github/workflows/ci.yml` |
| Procedimientos y estándares de Pruebas | IEEE Std 829-2008 (documentación de pruebas de software); plantilla «Formato_ieee829» del Politécnico (Drive del proyecto) |
| Metodologías y estándares | IEEE Std 830-1998; Ley 1581 de 2012; Crispin, L. y Gregory, J. (2009). *Agile Testing*. Addison-Wesley; Cohn, M. (2009). *Succeeding with Agile* (pirámide de automatización) |
| Datos | Karnik et al. (2025), doi:10.1038/s41597-025-04868-2; Hansen et al. (2013), Global Forest Change |

## 9. Glosario

| Término | Definición |
|---|---|
| Caso de prueba (CP) | Conjunto de precondiciones, pasos, datos y resultado esperado para verificar un requisito |
| Prueba unitaria | Verifica una función o clase aislada, sin red ni base de datos externa |
| Prueba de integración | Verifica varios componentes juntos (API, base SQLite en memoria, servicios) |
| Prueba de extremo a extremo (E2E) | Recorre el sistema completo desde el navegador hasta la base de datos |
| Prueba de regresión | Repite pruebas ya aprobadas para comprobar que un cambio no rompió lo existente |
| Caso golden | Polígono de referencia con resultado esperado conocido |
| Doble de prueba | Componente simulado que reemplaza un servicio externo (satélite `fake`, modelo guionizado, correo en memoria) |
| Cobertura | Porcentaje de líneas del código ejecutadas por las pruebas |
| Incidencia | Diferencia entre el resultado obtenido y el esperado, registrada para su corrección |
| Severidad | Impacto de una incidencia: crítica, alta, media o baja |
| Bloqueado | Caso que no puede ejecutarse por una dependencia externa |
| Partición de equivalencia / valores límite | Técnicas para elegir datos de prueba representativos y en los bordes de los rangos |
| NDVI | Índice de Vegetación de Diferencia Normalizada |
| T0 | Fecha de inicio o certificación del proyecto, a partir de la cual se compara |
| Índice de credibilidad | Correspondencia entre lo declarado y lo observado, en escala de 0 a 1 |
| HMAC | Código de autenticación de mensajes con clave; se usa para no guardar el teléfono y para firmar el webhook y la sesión |
| scrypt | Función de derivación de claves usada para guardar contraseñas |
| Token de un solo uso | Enlace de recuperación o invitación que vence y no puede reutilizarse (RF09) |
| Verificación en dos pasos (2FA) | Segundo factor: además de la contraseña se pide un código temporal enviado al correo |
| SMTP | Protocolo de envío de correo; STARTTLS y SSL cifran la conexión |
| JUnit XML | Formato estándar de reporte de resultados de pruebas |
