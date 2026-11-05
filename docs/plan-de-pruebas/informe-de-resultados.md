# Informe de resultados de pruebas

Ejecución completa del [plan de pruebas](plan-de-pruebas.md), versión 1.3, sobre la rama `main` el 05/11/2026 (la primera ejecución fue el 03/11/2026). Entorno: Linux, Python 3.12, Node 22, Chromium con Playwright; base SQLite en memoria y PostgreSQL 16 (pruebas automáticas), bases temporales (E2E y mediciones) y producción en Vercel con Supabase (mediciones con Gemini real y correo SMTP).

## 1. Resumen

| Indicador | Resultado |
|---|---|
| Casos especificados | 64 |
| Casos aprobados | 61 (95 %) |
| Casos fallidos | 0 |
| Casos bloqueados por dependencias externas | 3 (CP-29 y CP-46 del piloto, CP-49 de WhatsApp); de CP-50 queda pendiente solo la evaluación formal de 20 casos |
| Requisitos funcionales RF01–RF09 con casos aprobados | 9 de 9 (100 %) |
| Pruebas automáticas del backend | 353 aprobadas, 0 fallidas, tanto en SQLite como en PostgreSQL 16 |
| Cobertura de líneas del backend | 89 % (5.893 sentencias) |
| Pruebas del sitio (Vitest) | 95 aprobadas en 10 archivos |
| Pruebas del panel | 5 aprobadas |
| Verificaciones E2E en navegador | 36 de 36 aprobadas |
| Análisis estático | `ruff` y `pyright`: 0 errores; `eslint` y `tsc`: 0 errores |
| Compilación de producción del sitio | Correcta |
| Asistente en producción con Gemini real | 17 consultas: 100 % bajo 10 s, p90 8,5 s, máximo 8,6 s |
| Incidencias registradas | 19 (todas cerradas; ver [`incidencias.md`](incidencias.md)) |

## 2. Resultados por suite

| Suite | Comando | Resultado | Evidencia |
|---|---|---|---|
| Backend: estilo | `uv run ruff check . && uv run ruff format --check .` | Sin errores, 170 archivos con formato | `evidencias/backend-ruff.txt` |
| Backend: tipos | `uv run pyright` | 0 errores | `evidencias/backend-pyright.txt` |
| Backend: pruebas y cobertura | `uv run pytest --cov=bosquevivo --junitxml=...` | 353 aprobadas en 47 s (124 unitarias y 229 de integración y regresión), cobertura 89 % | `evidencias/backend-pytest.txt`, `backend-junit.xml` |
| Backend en PostgreSQL 16 | `TEST_DATABASE_URL=postgresql://… uv run pytest` | 353 aprobadas en 69 s | `evidencias/backend-postgres-junit.xml` |
| Sitio: estilo | `npm run lint` | Sin errores | `evidencias/web-lint.txt` |
| Sitio: pruebas | `npx vitest run` | 95 aprobadas | `evidencias/web-vitest.txt`, `web-junit.xml` |
| Sitio: compilación | `npm run build` | Correcta, incluidas `/terminos`, `/privacidad` y `/uso-de-datos` | `evidencias/web-build.txt` |
| Panel | `uv run pytest` | 5 aprobadas | — |
| E2E | `docs/plan-de-pruebas/scripts/ejecutar-e2e.sh` | 36 de 36 | `evidencias/e2e-salida.txt`, `e2e-resultados.json`, `evidencias/capturas/` |

### Cobertura de los módulos nuevos o modificados

| Módulo | Cobertura |
|---|---|
| `accounts/service.py` (RF09, 2FA, avisos, invitaciones) | 99 % |
| `accounts/templates.py` (plantilla de correo de la marca) | 100 % |
| `accounts/mailer.py` (SMTP) | 98 % |
| `setup.py` (configuración automática) | 99 % |
| `api/routers/auth.py` | 91 % |
| `api/routers/admin.py` (incluye la consulta de incidentes) | 95 % |
| `accounts/passwords.py` | 95 % |
| `ai/agent/loop.py` | 98 % |
| `ai/llm/budget.py` (presupuesto de tiempo) | 100 % |
| `ai/llm/gemini.py` (cambio de modelo y corte por tiempo) | 84 % |
| `core/incidents.py` | 100 % |
| `satellite/ndvi.py`, `satellite/service.py` | 100 % |
| `assistant/dialogue.py` | 98 % |
| `assistant/service.py` | 95 % |
| `assistant/community.py` | 90 % |
| `registry/importer.py` | 87 % |
| `api/routers/community.py` | 100 % |

La cobertura más baja corresponde a clientes de servicios externos que no se llaman en las pruebas por diseño (`satellite/providers/gee.py` y `assistant/client.py` de Meta).

## 3. Mediciones de requisitos no funcionales

Comando: `uv run bosquevivo medir-rnf --rounds <n> --projects 3`. El asistente se mide con las intenciones del ERS (estado, alertas, ayuda) y dos preguntas libres; sin clave de Gemini las preguntas libres usan la respuesta de respaldo. En producción se midieron 8 preguntas libres al chat del auditor y 9 mensajes al chat comunitario (intenciones del ERS y dos preguntas libres), con Gemini real.

| Requisito | Meta | Datos simulados (`rnf-fake.json`) | Datos abiertos reales (`rnf-open.json`) | Producción con Gemini real (`rnf-produccion.json`) | Cumple |
|---|---|---|---|---|---|
| 3.3.1 Respuesta del asistente | ≥ 90 % en < 10 s | 100 consultas: p50 0,002 s, p90 0,005 s, máx. 0,009 s, 100 % < 10 s | 20 consultas: p90 0,005 s, 100 % < 10 s | 17 consultas: p50 0,6 s, p90 8,5 s, máx. 8,6 s, 100 % < 10 s; intenciones del ERS en 0,1–0,5 s | Sí |
| 3.3.1 Cálculo del índice | < 5 min por polígono | 0,04–0,05 s | 43,7 s, 44,7 s y 62,9 s (MODIS 250 m + Hansen, descarga real) | — | Sí |
| 3.3.3 Determinismo | Mismo índice con los mismos insumos | 99,9/99,9; 100/100; 100/100 | 97,2/97,2; 96,0/96,0; 56,1/56,1 | — | Sí |
| 3.3.3 Incidentes críticos | ≤ 2 al mes | — | — | 0 críticos en producción (`GET /api/v1/admin/incidents`) | Se mide en el piloto (CP-46) |
| 3.3.4 Disponibilidad | 95 % en el horario del piloto | — | — | — | Se mide en el piloto (CP-46) |

**Gemini saturado (INC-19).** La primera medición en producción del 05/11/2026 encontró los dos modelos gratuitos de Gemini respondiendo 503 por alta demanda: las preguntas libres tardaron entre 12 y 61 s (solo el 41 % bajo 10 s). Con el presupuesto de 8 s por respuesta, todas las consultas quedaron bajo 10 s; mientras dure la saturación, las preguntas libres del auditor se responden con el texto de respaldo y el chat comunitario respondió una pregunta libre con Gemini en 4,1 s. La mañana del mismo día, con el servicio normal, las preguntas al agente tardaron 3–5 s con Gemini (CP-50).

## 4. Pruebas de extremo a extremo

`scripts/ejecutar-e2e.sh` crea una base temporal con los proyectos de demostración, invita una cuenta de auditor (`bosquevivo user-invite`), activa la verificación en dos pasos con el buzón local (`AUTH_TWO_FACTOR=on`), levanta la API y el sitio compilado, y recorre en Chromium:

| Flujo | Casos | Resultado |
|---|---|---|
| Invitación: correo con enlace, bienvenida, primera contraseña | CP-56 | 3 verificaciones aprobadas |
| Recuperación de contraseña (RF09): acceso restringido, credenciales inválidas, mensaje genérico, enlace por correo, token inválido, contraseñas distintas y débiles, actualización, enlace reutilizado | CP-30 a CP-36 | 10 verificaciones aprobadas |
| Verificación en dos pasos y avisos: código por correo, código incorrecto, reenvío, entrada con la contraseña nueva, sesión con el correo, aviso de inicio de sesión, aviso de cambio de contraseña, correos con HTML, plantilla de la marca con enlaces legales | CP-37, CP-53 a CP-55, CP-64 | 9 verificaciones aprobadas |
| Chat en línea (RF07, RF08, Ley 1581): saludo y aviso, consentimiento, ayuda, registro del proyecto, estado, lenguaje sencillo, alertas, consulta no reconocida, borrado | CP-21 a CP-28, CP-42 | 9 verificaciones aprobadas |
| Documentos legales: términos, política de privacidad y uso de datos con versión, fecha y contenido mínimo; enlaces en el pie y en el chat en línea | CP-63 | 5 verificaciones aprobadas |

Capturas: `evidencias/capturas/00-invitacion-activada.png` a `09-uso-de-datos.png`.

Prueba manual adicional (CP-58): `scripts/start.sh` en un clon sin `.env` generó los secretos, la base y los datos de demostración, compiló el sitio y dejó la API (`/health`), el sitio y el chat en línea respondiendo en modo producción.

## 4.1 PostgreSQL y despliegue

| Prueba | Resultado |
|---|---|
| Suite completa contra PostgreSQL 16 (`TEST_DATABASE_URL`) | 353 de 353 aprobadas |
| `migrate-db` de una base SQLite con datos de demostración, cuentas e invitaciones | 233 filas en 21 tablas; registros nuevos sin conflicto de secuencias |
| Entorno solo con el núcleo de dependencias | 274 MB (límite de Vercel: 500 MB) |
| API en modo Vercel (`VERCEL=1`) contra PostgreSQL | `/health`, proyectos, reporte PDF y HTML generados al vuelo, chat comunitario; auditoría rechazada con el mensaje de usar la CLI |
| Producción (Vercel + Supabase) | Sitio https://bosque-vivo-web.vercel.app y API https://bosque-vivo-api.vercel.app; 58 proyectos; `/proyectos` en 1–2 s; reporte PDF, chat en línea, acceso con verificación en dos pasos y documentos legales responden; despliegue automático desde `main` |
| Correo SMTP real (CP-57) | Códigos de verificación, aviso de inicio de sesión y correo de prueba (`POST /api/v1/admin/mail-test`) entregados en Gmail con la plantilla nueva |

## 5. Evaluación de los criterios de aceptación

| Criterio (plan, 4.5.1) | Resultado | Cumple |
|---|---|---|
| 1. 100 % de pruebas automáticas aprobadas y análisis estático sin errores | 353 (SQLite y PostgreSQL) + 95 + 5 aprobadas, 0 errores | Sí |
| 2. Cobertura del backend ≥ 80 % | 89 % | Sí |
| 3. RF01–RF09 con al menos un caso aprobado | 9 de 9 | Sí |
| 4. Casos de prioridad 1 y 2 ejecutados | Todos, salvo CP-29 (usuarios del piloto) | Sí, con la excepción prevista |
| 5. 0 incidencias críticas o altas abiertas | 0 abiertas | Sí |
| 6. Rendimiento | 100 % < 10 s (también en producción con Gemini real); máximo 62,9 s por polígono | Sí |
| 7. Determinismo | 3 de 3 | Sí |
| 8. Compilación de producción | Correcta | Sí |

**Conclusión.** Se cumplen los criterios para dar por completado el plan en esta etapa. Quedan tres casos bloqueados por dependencias externas (credenciales de Meta para WhatsApp y usuarios del piloto) y el informe formal de `bosquevivo eval` de CP-50; tienen guía de ejecución en [`docs/guias`](../guias) y en este plan, y no afectan los requisitos funcionales comprometidos, que se verificaron sin ellos. La calidad de las respuestas libres depende de la disponibilidad de la capa gratuita de Gemini; cuando está saturada, el sistema responde a tiempo con el respaldo.

## 6. Cómo repetir la ejecución

```bash
cd backend
uv run ruff check . && uv run ruff format --check . && uv run pyright
uv run pytest --cov=bosquevivo
SATELLITE_PROVIDER=open uv run bosquevivo medir-rnf --rounds 100 --projects 3
```

```bash
cd web
npm run lint && npx next typegen && npm run typecheck && npm test && npm run build
```

```bash
bash docs/plan-de-pruebas/scripts/ejecutar-e2e.sh
```

Incidentes registrados en producción:

```bash
curl -H "X-Admin-Token: $ADMIN_TOKEN" "https://bosque-vivo-api.vercel.app/api/v1/admin/incidents?days=30"
```
