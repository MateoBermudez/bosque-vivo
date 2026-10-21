# Bosque Vivo — Plan de implementación (v3: local + Gemini)

> Proyecto Integrador · Ingeniería Informática · ODS 15 · Politécnico Colombiano Jaime Isaza Cadavid
> Equipo: 4 personas · Versión 3 · 20-oct-2026
> Documento complementario con el diseño del agente: [`PLAN_AGENTE_IA.md`](PLAN_AGENTE_IA.md)

## 0. Decisiones vigentes

Estas decisiones las tomó el equipo y mandan sobre cualquier otra parte de este documento.

| Tema | Decisión |
|---|---|
| **Dónde corre** | **100 % local, en este computador** (Windows 11 Pro; i5-13420H de 8 núcleos / 12 hilos; 31,7 GB de RAM; sin GPU dedicada; ~300 GB libres). **Sin máquinas virtuales, sin servidores, sin nube propia.** |
| **Docker** | **No se usa.** Está instalado, pero en Windows corre sobre WSL2/Hyper-V (una VM). Todo se ejecuta como procesos normales de Windows. |
| **IA** | **Gemini de Google AI Studio, capa gratuita, por API.** **No se usa Ollama ni modelos locales.** El nombre del modelo va en una variable de entorno (los modelos y sus cuotas cambian; verificar en AI Studio). |
| **Escala** | **Proyecto universitario, no tesis.** Mínimo viable defendible y bien probado, no un producto de producción. Se prioriza que funcione, se pueda demostrar y esté documentado. |
| **Código abierto (OE2)** | Todo el código propio es abierto. Gemini, Google Earth Engine y WhatsApp Cloud API son **servicios gratuitos de terceros**, como ya contempla el ERS ("apoyado en servicios gratuitos de terceros"). Se documenta en un ADR. |
| **Alcance** | ERS (RF01–RF08) + agente de IA que razona, analiza imágenes y concluye con evidencia (ver `PLAN_AGENTE_IA.md`). |

## 1. Base del plan

Fuentes: ERS (resumen en láminas, estructura IEEE 830), documento de objetivos y documento interno "Bosque Vivo".

- **Requisitos del ERS:**
  - RF01 Importar polígonos públicos · RF02 Obtener series satelitales · RF03 Calcular NDVI · RF04 Comparar declarado y observado · RF05 Calcular índice de credibilidad · RF06 Generar reporte de auditoría · RF07 Recibir consultas por WhatsApp · RF08 Responder en lenguaje sencillo.
  - NFR: 90 % de consultas del asistente en < 10 s · índice completo en ≤ 5 min por polígono (meta a validar) · 95 % de disponibilidad en horario de piloto · ≤ 2 incidentes críticos por mes · TLS 1.2+ · Ley 1581 de 2012 (finalidad, autorización previa, supresión).
- **Delimitación metodológica del ERS:** el índice mide correspondencia entre lo declarado y lo observado. **No estima contrafactuales ni adicionalidad.**
- **Objetivos específicos:** OE1 documentar (ERS) · OE2 diseñar con herramientas de código abierto · OE3 desarrollar · OE4 validar con plan de pruebas.
- **Plazo asumido:** ~8 semanas desde hoy. Falta confirmar la fecha real.

> **Alcance frente al ERS.** El ERS deja fuera la detección temprana y no menciona análisis de imágenes con IA. El agente de IA amplía el ERS: hay que presentarlo al docente y, si lo aprueba, agregar los RF09–RF17 como revisión del ERS (control de cambios del OE1).

---

## 2. Arquitectura (todo en un solo PC)

Un **monolito modular** en un monorepo: una sola aplicación Python con módulos de fronteras claras, más un panel. Sin microservicios, sin colas externas, sin base de datos como servidor.

```
 Registros públicos ─▶ [registry] ─▶ SQLite ◀─ [satellite] ◀─ Google Earth Engine
 (Karnik 2025, Verra,        │          ▲        (Sentinel-2, Landsat, Hansen GFC)
  Gold Standard)             ▼          │
                     [audit: declarado vs observado → índice]
                              │                  │
                     [reports HTML/PDF]     API local (FastAPI) ◀──▶ [agente + Gemini API]
                                                │            │
                                  Panel web (Streamlit)   Webhook WhatsApp ◀── túnel (ngrok/cloudflared)
                                  + chat del auditor                              ▲
                                                                        Meta WhatsApp Cloud API
```

**Procesos que se ejecutan en el PC:**

1. `api`: FastAPI (REST + webhook de WhatsApp) con un trabajador de tareas en segundo plano.
2. `panel`: Streamlit (solo lectura + chat del auditor).
3. `tunnel`: ngrok o cloudflared, solo cuando se necesita recibir mensajes de WhatsApp.

Un script (`scripts/dev.ps1`) los arranca juntos.

### 2.1 Stack

| Capa | Elección | Por qué |
|---|---|---|
| Lenguaje | **Python 3.12** (ya instalado). `uv` para dependencias, `ruff`, `pytest`, `pyright` | Todo el ecosistema geoespacial y el SDK de Gemini están en Python. Un solo lenguaje para 4 personas. |
| API | **FastAPI + Pydantic v2** | OpenAPI automático; contratos claros entre módulos. |
| Base de datos | **SQLite** (SQLAlchemy 2). Consultas espaciales con **shapely** (índice `STRtree` en memoria) | Cero instalación. Con 10–60 polígonos no hace falta PostGIS. Si algún día hace falta, el cambio es acotado. |
| Tareas largas | **Trabajador propio en segundo plano** (tabla `job` en SQLite + hilo/proceso) y `APScheduler` para tareas periódicas | Celery y Redis no funcionan bien en Windows nativo. |
| Satélite | **Google Earth Engine** (`earthengine-api`) detrás de una interfaz `SatelliteProvider` | El ERS ya lo cita. La interfaz permite cambiarlo si hace falta. |
| Geo / análisis | geopandas, shapely, pyproj, numpy, scipy, `pymannkendall` | Tendencias y detección de cambio. |
| IA | **Gemini (Google AI Studio)** con el SDK oficial `google-genai`: llamado a funciones, salida estructurada, imágenes, audio y PDF | Un solo servicio para razonar, ver imágenes, entender audio y leer PDFs. Detalle en `PLAN_AGENTE_IA.md`. |
| Reportes | Jinja2 → HTML; PDF con `fpdf2` o ReportLab (Python puro) | **Evitar WeasyPrint en Windows**: necesita librerías del sistema que dan problemas. |
| Panel | **Streamlit** + pydeck/folium + Altair/Plotly | Coincide con el documento interno (que menciona Streamlit), es Python puro y trae chat listo (`st.chat_message`). Next.js queda como mejora solo si sobra tiempo. |
| WhatsApp | **Meta WhatsApp Cloud API** con el número de prueba; plan B: Twilio Sandbox | El webhook llega al PC por túnel HTTPS. |
| Túnel | **ngrok** (dominio estático gratuito) o **cloudflared** | Exponer el webhook sin servidor. El túnel aporta el HTTPS. Verificar condiciones vigentes. |
| Observabilidad | Logs JSON (structlog) + tablas de trazas en SQLite + página `/admin/trazas` en el panel | Sin Langfuse ni Sentry: requieren más infraestructura. |
| CI | GitHub Actions: `ruff` + `pytest` | Solo verifica el código; no despliega nada. |

### 2.2 Estructura del repositorio

```
bosque-vivo/
├─ README.md
├─ PLAN_IMPLEMENTACION.md  PLAN_AGENTE_IA.md
├─ docs/
│  ├─ ers/             ERS + matriz de trazabilidad
│  ├─ architecture/    diagramas (contexto y contenedores) + ADRs
│  ├─ methodology/     definición del índice y limitaciones
│  ├─ testing/         plan de pruebas (OE4) y resultados
│  └─ privacy/         aviso y política (Ley 1581)
├─ backend/
│  ├─ pyproject.toml
│  ├─ src/bosquevivo/
│  │  ├─ core/         config (.env), logging, errores
│  │  ├─ db/           modelos, sesión, repositorios
│  │  ├─ registry/     RF01  importadores (karnik, verra, gold_standard), validación de geometrías
│  │  ├─ satellite/    RF02-03  providers/gee, máscara de nubes, NDVI, compuestos, miniaturas, caché
│  │  ├─ audit/        RF04-05  declared, observed, compare, index/(componentes, pesos, versiones)
│  │  ├─ reports/      RF06  plantillas y generación de reportes
│  │  ├─ ai/           agente, herramientas, prompts, guardas, evaluación (ver PLAN_AGENTE_IA.md)
│  │  ├─ assistant/    RF07-08  WhatsApp (cliente, webhook, firma), diálogo, consentimiento
│  │  ├─ jobs/         trabajador en segundo plano y tareas
│  │  └─ api/          routers v1, schemas, dependencias
│  └─ tests/           unit · integration · golden · eval
├─ panel/              Streamlit
├─ notebooks/          exploración (solo exploración; lo útil pasa a backend/)
├─ data/               ignorado por git (bosquevivo.db, caché de imágenes)
├─ seed/               datos semilla pequeños o enlace a la base compartida
├─ scripts/            dev.ps1, import, benchmark
└─ .github/            workflows, plantillas de PR/issue, CODEOWNERS
```

**Fronteras entre módulos:** `api → servicios → db`. El agente solo llama herramientas registradas, y esas herramientas leen vía `audit.queries` o `satellite`. Cada módulo expone una interfaz pública en su `__init__.py`.

### 2.3 Cómo trabaja un equipo de 4 con todo en local

- **Desarrollo:** cada integrante corre el sistema en su propio PC, con su propio `.env` y su propia clave gratuita de AI Studio.
- **Demo y piloto:** corren **en este computador** (la instancia "oficial").
- **Datos compartidos:** la base SQLite con proyectos y resultados ya calculados **no va en git**. Se comparte como archivo semilla (Drive o asset de GitHub Releases), para que nadie tenga que recalcular todo con GEE.
- **Secretos:** `.env` nunca se sube (`.gitignore`). Se versiona `.env.example`.
- **Variables:** `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_MODEL_LIGHT`, `GEE_PROJECT`, `WHATSAPP_TOKEN`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `PHONE_HMAC_KEY`, `ADMIN_TOKEN`.

### 2.4 Particularidades de Windows

- Usar PowerShell para los scripts; rutas con `pathlib`.
- Evitar dependencias que exijan compilar o instalar librerías del sistema (WeasyPrint, Redis, Celery).
- `geopandas`/`shapely`/`pyogrio` instalan por *wheels*; no hace falta GDAL aparte.
- **Para el piloto:** el PC debe estar encendido, sin suspensión y con Internet estable. Ese es el único "servidor".

---

## 3. Datos y modelo (SQLite)

| Tabla | Campos principales |
|---|---|
| `project` | registro, id_registro, nombre, país, tipo, año_inicio, area_ha, `geom` (WKB/GeoJSON), fuente, versión_fuente |
| `project_declaration` | project_id, campo, valor, documento_fuente, capturado_por (captura manual o extracción asistida revisada) |
| `ndvi_observation` | project_id, periodo, sensor, ndvi_media / p10 / p90, frac_píxeles_válidos, n_escenas |
| `forest_loss` | project_id, año, ha_perdidas, fuente |
| `audit_run` | id, project_id, estado, parámetros (JSON), git_sha, versiones de datasets (JSON), duración, `index_version` |
| `audit_result` | run_id, índice 0-100, categoría, componentes (JSON), confianza, narrativa |
| `report` | run_id, formato, ruta, hash |
| `image_asset` | proyecto, fechas, sensor, tipo (color natural / falso color / NDVI), ruta, hash |
| `evidence` | id, tipo (auditoría, serie, imagen, foto de usuario), referencia, hash |
| `agent_run` / `agent_step` | consulta, rol, clase, modelo, versión de prompt, herramientas llamadas, latencia, resultado del validador |
| `job` | tipo, payload, estado, intentos, resultado |
| `wa_user` / `consent_log` | teléfono como HMAC, consentimiento (versión del aviso, fecha), `deleted_at` |
| `kb_chunk` | fragmento, fuente, embedding (opcional) |

`audit_run` guarda parámetros, SHA del código y versiones de los datos: eso es la trazabilidad y reproducibilidad que pide el ERS.

---

## 4. Metodología del índice (RF04–RF05)

Es lo más delicado del proyecto y no depende de código.

**Propuesta v0, a validar con el docente antes de la semana 3:**

| Componente | Peso | Qué mide | Fuente |
|---|---|---|---|
| Permanencia forestal | 50 % | Porcentaje del bosque inicial que sigue en pie desde la fecha de acreditación (T0) | Hansen GFC (`lossyear`, `treecover2000`) y NDVI |
| Tendencia de vigor | 25 % | Pendiente NDVI posterior a T0 (Theil-Sen + Mann-Kendall) frente a la anterior | Sentinel-2 / Landsat |
| Estabilidad | 25 % | Ausencia de caídas abruptas de NDVI posteriores a T0 (punto de cambio) | Serie NDVI |

- **Salida:** puntaje 0–100 y categoría (Alta / Media / Baja / Insuficiente).
- **La confianza va aparte** (píxeles válidos, número de escenas, nubosidad). En Amazonía y zona andina las nubes dejan series incompletas: "datos insuficientes" es un resultado legítimo.
- **Lo declarado** entra como T0, área y, cuando exista, la línea base del PDD (captura manual o extracción asistida con revisión humana).
- Pesos y umbrales en configuración versionada (`index_version`) y análisis de sensibilidad en el reporte.
- **Lenguaje neutro** en todo el producto: "correspondencia observada", nunca "fraude".

**Validación:** 10–15 polígonos con comportamiento conocido (intactos, con pérdida documentada, con nubosidad extrema) para calibrar y probar el índice.

---

## 5. Requisitos

### 5.1 Del ERS (RF01–RF08)

| RF | Entrega | Detalle técnico |
|---|---|---|
| **RF01** Importar polígonos | CLI y endpoint admin que cargan la base de Karnik et al. (2025, ~575 proyectos), filtrable por país | Validar y reparar geometrías (`make_valid`), reproyectar, calcular área, deduplicar. Guardar versión de la fuente. |
| **RF02** Series satelitales | `SatelliteProvider.get_timeseries(geom, rango, sensor)` | GEE: S2 SR Harmonized (con Cloud Score+ o banda SCL) y Landsat C2 L2, más Hansen GFC. Compuestos mensuales por mediana, escala adaptativa según el tamaño. **Verificar los IDs de dataset vigentes.** |
| **RF03** NDVI | Función pura y testeable, con caché | Cada sensor por separado (Landsat para el histórico, S2 desde 2017). |
| **RF04** Declarado vs observado | `audit.compare` | Tabla declarado/observado por periodo. |
| **RF05** Índice | `IndexCalculator` versionado | Sección 4. |
| **RF06** Reporte | HTML y PDF | Gráficos, componentes, confianza, parámetros, git SHA, versiones de datos, limitaciones. |
| **RF07** Recibir consultas | Webhook con firma validada, `200` inmediato, procesamiento en segundo plano | Idempotencia por `message_id`. Texto, ubicación, y fotos/audio según el nivel. |
| **RF08** Lenguaje sencillo | Respuestas ≤ 300 caracteres en español colombiano cotidiano | El agente redacta; el validador comprueba las cifras. Probar con 5 personas no técnicas. |

### 5.2 Ampliación con el agente de IA (RF09–RF17)

Detalle en `PLAN_AGENTE_IA.md`. Resumen y prioridad:

| ID | Requisito | Nivel |
|---|---|---|
| RF09 | Agente con razonamiento multi-paso y herramientas | **Núcleo** |
| RF15 | Base de conocimiento con citas (metodología, glosario, normativa) | **Núcleo** |
| RF17 | Chat técnico del auditor en el panel | **Núcleo** |
| RF10 | Análisis visual antes/después y calidad de imagen con Gemini | Alta |
| RF12 | Fotos y ubicación del usuario como evidencia no verificada | Media |
| RF13 | Voz: notas de audio entendidas por Gemini | Media |
| RF16 | Extracción de declaraciones desde PDD con revisión humana | Media |
| RF14 | Alertas tempranas opt-in (Sentinel-2 + NASA FIRMS) | Opcional |
| RF11 | Modelo propio de visión (entrenado) | Opcional / evolución futura |

---

## 6. Equipo (4 personas)

| Persona | Rol | Dueño de | Suplente |
|---|---|---|---|
| **P1** | Plataforma e integración (tech lead) | Repo, CI, núcleo de la API, base de datos, trabajador en segundo plano, script de arranque, **webhook de WhatsApp y túnel**, **capa de acceso a Gemini** (cuotas, caché, reintentos), consentimiento y borrado (Ley 1581), mediciones de NFR | P2 |
| **P2** | Datos geoespaciales | RF01, RF02, RF03, `SatelliteProvider`, miniaturas de imágenes, caché, (FIRMS si hay tiempo) | P3 |
| **P3** | Analítica y reportes | RF04, RF05, RF06, metodología, conjunto de validación, evaluación del análisis visual | P2 |
| **P4** | Agente y experiencia | Bucle del agente, herramientas, prompts, validador de fidelidad, base de conocimiento, panel Streamlit y chat, diálogo de WhatsApp | P1 |

**Contratos que se congelan en la semana 0** (para trabajar en paralelo con datos simulados): esquema de BD, OpenAPI v0, interfaz `SatelliteProvider`, `AuditSummary`, esquema de herramientas del agente, formato de evidencia y de traza.

### 6.1 Flujo de trabajo

- Ramas cortas desde `main` (`feat/rf03-ndvi-sentinel2`), PR con 1 revisor distinto del autor, `main` protegido, commits convencionales.
- Cada issue lleva etiqueta `RFxx` / `RNFx`; la matriz de trazabilidad se mantiene con esas etiquetas.
- `pre-commit` (ruff, pyright). Plantilla de PR con checklist.
- **Definition of Done:** tests pasan, tipado limpio, OpenAPI actualizado, documentación mínima, demo funcionando en local, revisado por otra persona.
- Tablero en GitHub Projects, sprints de 1 semana (daily asíncrono de 10 min por chat; demo e integración los viernes).

---

## 7. Pruebas (OE4) y NFR en un PC local

| NFR del ERS | Cómo se mide en local |
|---|---|
| 90 % de consultas < 10 s | Script de carga con ≥ 100 consultas rápidas (precalculadas). Se mide p50/p90 incluyendo la llamada a Gemini. Las consultas profundas se miden aparte (clase "profunda", sección 5 de `PLAN_AGENTE_IA.md`). |
| Índice por polígono en ≤ 5 min | Benchmark con polígonos chicos, medianos y grandes; reportar la distribución. |
| 95 % de disponibilidad en horario de piloto | Registro de latidos (`/health`) cada minuto durante el piloto, más un monitor externo gratuito sobre la URL del túnel si se desea. El PC no debe suspenderse. |
| ≤ 2 incidentes críticos por mes | Bitácora de incidentes. |
| TLS 1.2+ | El HTTPS lo termina el túnel (ngrok/Cloudflare). Se verifica con `testssl.sh` o SSL Labs sobre la URL pública. Entre el túnel y el PC el tráfico va por loopback. |
| Ley 1581 | Pruebas de consentimiento, supresión y retención; aviso publicado. |

**Capas de prueba:**
- **Unitarias** (`pytest`): objetivo ~60–70 % en `satellite`, `audit` y `ai`.
- **Integración:** SQLite en memoria y GEE simulado.
- **Golden tests:** los 10–15 polígonos de validación con resultados esperados.
- **Evaluación de IA:** ver `PLAN_AGENTE_IA.md`.
- **E2E:** diálogos guionizados de WhatsApp y del chat.
- **UAT:** piloto con voluntarios.

**Entregable OE4:** plan de pruebas con matriz **RF → casos de prueba → resultados**.

---

## 8. Cronograma (8 semanas)

| Fase | Objetivo | Entregable / demo |
|---|---|---|
| **S0** (3 días) | Arranque | Entorno local listo (sección 10), repo, CI, cuentas (GEE, AI Studio, Meta, túnel), contratos congelados, propuesta de ampliación del ERS al docente, ADRs, índice v0 |
| **S1–S2** | **Esqueleto andante** | Un proyecto de punta a punta: importar polígono → NDVI con GEE → SQLite → índice trivial → agente con 3–4 herramientas respondiendo por el chat del panel y por WhatsApp (túnel), con validador de fidelidad activo y ~20 preguntas de evaluación |
| **S3–S4** | **Núcleo completo** | 10–20 proyectos, índice v1 con confianza, todas las herramientas de datos, base de conocimiento, consentimiento y borrado, evaluación v1 (30–40 casos) |
| **S5–S6** | Visión y reportes | Miniaturas antes/después y calidad de imagen con Gemini (RF10), reportes, y 1–2 funciones medias (fotos, voz o PDD) |
| **S7** | **OE4** | Plan de pruebas, medición de NFR, evaluación de IA completa, piloto con ≤ 5 voluntarios |
| **S8** | Cierre | Documento de arquitectura, resultados, demo final, margen |

**Mapeo a objetivos:** OE1 ERS + revisión · OE2 diagramas y ADRs (S0–S2) · OE3 código · OE4 S7.

**Orden de recorte si falta tiempo:** RF14 alertas → RF11 → RF16 → RF13 voz → RF12 fotos → RF10 visión. **No se recorta:** el esqueleto andante, el agente con validador de fidelidad, el índice con confianza, la Ley 1581 y las pruebas de OE4.

---

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| **Cuotas de la capa gratuita de Gemini** (peticiones por minuto y por día) | Tope de pasos por consulta, caché de respuestas y de evaluación, reintentos con espera, modelo ligero para el router, respuesta de respaldo determinista cuando se agote la cuota |
| **Cambios de modelo o de condiciones del servicio gratuito** | Modelo en variable de entorno, interfaz `LLMProvider` delgada, prompts versionados |
| **Privacidad: la capa gratuita puede usar el contenido para mejorar productos de Google** (verificar términos vigentes) | No enviar teléfonos ni nombres; aviso de privacidad que menciona el procesamiento por un tercero; pruebas con voluntarios informados; fotos solo con consentimiento específico; consultar con el docente por la transferencia internacional (Ley 1581) |
| **El PC es el único servidor** | Sin suspensión durante el piloto, copia de seguridad de `bosquevivo.db`, base semilla compartida, modo demo con datos precalculados |
| **El túnel cambia de URL o falla** | ngrok con dominio estático o plan B de chat web; el chat del panel funciona sin WhatsApp |
| **Meta limita el número de prueba** (pocos destinatarios; verificar el límite) | Piloto con ≤ 5 voluntarios; Twilio Sandbox como plan B |
| **Cuota o autenticación de GEE** | Registrar el proyecto de GEE en S0, caché agresiva, interfaz `SatelliteProvider` |
| **Nubes en Amazonía y Andes** | Compuestos, confianza explícita, "datos insuficientes" como resultado válido |
| **El agente alucina cifras o acusa** | Validador de fidelidad, política de lenguaje neutro, respaldo determinista |
| **Formato de la base de Karnik no es el esperado** | Descargarla y revisarla en S0 |
| **El índice se percibe como acusación** | Lenguaje neutro y limitaciones visibles |
| **Ampliar demasiado el alcance** | Niveles Núcleo / Alta / Media / Opcional; el piloto no se mueve |
| **Un integrante no disponible** | Suplentes, PRs pequeños, documentación mínima por módulo |

---

## 10. Primeros 3 días (S0)

**Preparar este PC (todos los demás hacen lo mismo en el suyo):**

1. Instalar `uv` (Python 3.12 ya está instalado). Node no es necesario.
2. Crear una clave gratuita en **Google AI Studio** y guardarla en `.env`.
3. Registrar el proyecto de **Earth Engine** (uso no comercial/académico) y autenticar con `earthengine authenticate`.
4. Instalar **ngrok** (cuenta gratuita, dominio estático) o cloudflared.
5. Crear la app de **Meta** (número de prueba) y registrar los números de los voluntarios.
6. Configurar la suspensión del PC para el piloto.

**Por persona:**

- **P1:** repo, CI mínimo, estructura del monorepo, `scripts/dev.ps1`, esqueleto FastAPI con `/health`.
- **P2:** probar GEE con un polígono (serie NDVI y miniatura); descargar la base de Karnik y reportar el esquema real.
- **P3:** escribir `docs/methodology/indice-v0.md` y llevarlo al docente.
- **P4:** definir el esquema de herramientas y la traza; primer prompt del agente con herramientas simuladas; esqueleto del panel Streamlit.
- **Todos (2 h):** congelar contratos y redactar los ADRs.

**ADRs iniciales:**
1. Monorepo y monolito modular.
2. Ejecución 100 % local, sin Docker ni VM.
3. SQLite + shapely en lugar de PostGIS.
4. Gemini (AI Studio, capa gratuita) como único proveedor de IA y su justificación frente al OE2.
5. GEE detrás de `SatelliteProvider`.
6. Streamlit para el panel.
7. WhatsApp Cloud API con túnel.

---

## 11. Preguntas abiertas

**Resueltas:**
- ~~¿GPU o servidor?~~ → Ninguno. Este PC y la API de Gemini.
- ~~¿El modelo de lenguaje debe ser abierto?~~ → No: Gemini, documentado como servicio gratuito de terceros.
- ~~¿Nivel del proyecto?~~ → Universitario, no tesis.

**Pendientes:**
1. ¿Cuál es la **fecha real de entrega**?
2. ¿El docente aprueba ampliar el ERS con el agente de IA (RF09–RF17) y el **índice v0**?
3. ¿El ERS completo trae criterios de aceptación o más RF?
4. ¿Hay 5 voluntarios (compañeros, familia o una comunidad) para el piloto y las pruebas de comprensión?
5. ¿El docente acepta que los mensajes de los voluntarios se procesen con un servicio externo (Gemini) con aviso y consentimiento?
