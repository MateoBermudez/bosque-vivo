# Informe de resultados de pruebas

Ejecución completa del [plan de pruebas](plan-de-pruebas.md), versión 1.4, sobre la rama `main` el 19/11/2026 (las anteriores fueron el 03/11 y el 05/11/2026). En esta versión el chat en línea reemplaza a WhatsApp con texto, ubicación, fotos y notas de voz, y se agregan CP-65 a CP-67. Entorno: Linux, Python 3.12, Node 22, Chromium con Playwright; base SQLite en memoria y PostgreSQL 16 (pruebas automáticas), bases temporales (E2E y mediciones) y producción en Vercel con Supabase (mediciones con Gemini real y correo SMTP).

## 1. Resumen

| Indicador | Resultado |
|---|---|
| Casos especificados | 65 |
| Casos aprobados | 65 (100 %) |
| Casos fallidos | 0 |
| Requisitos funcionales RF01–RF09 con casos aprobados | 9 de 9 (100 %) |
| Pruebas automáticas del backend | 360 aprobadas, 0 fallidas, tanto en SQLite como en PostgreSQL 16 |
| Cobertura de líneas del backend | 89 % (5.944 sentencias) |
| Pruebas del sitio (Vitest) | 100 aprobadas en 12 archivos |
| Pruebas del panel | 5 aprobadas |
| Verificaciones E2E en navegador | 48 de 48 aprobadas (incluye el chat en un celular de 390 px con ubicación, foto y nota de voz) |
| Análisis estático | `ruff` y `pyright`: 0 errores; `eslint` y `tsc`: 0 errores |
| Compilación de producción del sitio | Correcta |
| Asistente en producción con Gemini real | 19/11/2026: 12 mensajes del chat en línea desde un celular (texto, ubicación, foto y nota de voz hablada): 100 % bajo 10 s, p50 0,3 s, p90 2,6 s, máximo 9,0 s. 05/11/2026: 17 consultas, 100 % bajo 10 s |
| Producción (19/11/2026, Next.js 16.4.6) | 15 de 15 verificaciones de `scripts/produccion.cjs`: sitio sin WhatsApp, chat en línea desde un celular y cuenta de pruebas sin código |
| Evaluación del asistente en producción (CP-50) | 16 de 20 casos; fidelidad, neutralidad, incertidumbre, sin fugas y longitud 100 %; herramientas 80 % (los 15 casos que respondió Gemini, aprobados; 5 con respaldo por la capa gratuita) |
| Incidencias registradas | 24 (todas cerradas; ver [`incidencias.md`](incidencias.md)) |

## 2. Resultados por suite

| Suite | Comando | Resultado | Evidencia |
|---|---|---|---|
| Backend: estilo | `uv run ruff check . && uv run ruff format --check .` | Sin errores, 170 archivos con formato | `evidencias/backend-ruff.txt` |
| Backend: tipos | `uv run pyright` | 0 errores | `evidencias/backend-pyright.txt` |
| Backend: pruebas y cobertura | `uv run pytest --cov=bosquevivo --junitxml=...` | 360 aprobadas en 39 s (124 unitarias, 227 de integración y regresión, 5 «golden» y 4 del arnés de evaluación), cobertura 89 % | `evidencias/backend-pytest.txt`, `backend-junit.xml` |
| Backend en PostgreSQL 16 | `TEST_DATABASE_URL=postgresql://… uv run pytest` | 360 aprobadas | `evidencias/backend-postgres-junit.xml` |
| Sitio: estilo | `npm run lint` | Sin errores | `evidencias/web-lint.txt` |
| Sitio: pruebas | `npx vitest run` | 100 aprobadas (incluye el WAV de las notas de voz y el envío de adjuntos) | `evidencias/web-vitest.txt`, `web-junit.xml` |
| Sitio: compilación | `npm run build` | Correcta con Next.js 16.4.6: 21 páginas, sin `/whatsapp` (redirige a `/asistente`) | `evidencias/web-build.txt` |
| Panel | `uv run pytest` | 5 aprobadas | — |
| E2E | `docs/plan-de-pruebas/scripts/ejecutar-e2e.sh` | 48 de 48 | `evidencias/e2e-salida.txt`, `e2e-resultados.json`, `evidencias/capturas/` |
| Evaluación del agente | `bosquevivo eval --remote https://bosque-vivo-api.vercel.app --pausa 30` | 16 de 20 | `evidencias/eval-produccion.json` |
| Producción | `node docs/plan-de-pruebas/scripts/produccion.cjs` | 15 de 15 | `evidencias/produccion-chat.json`, `capturas/11-chat-produccion.png` |

### Cobertura de los módulos nuevos o modificados

| Módulo | Cobertura |
|---|---|
| `accounts/templates.py` (plantilla de correo de la marca) | 100 % |
| `accounts/mailer.py` (SMTP) | 98 % |
| `setup.py` (configuración automática) | 99 % |
| `api/routers/auth.py` | 91 % |
| `api/routers/admin.py` (incluye la consulta de incidentes) | 95 % |
| `accounts/passwords.py` | 95 % |
| `ai/agent/loop.py` | 98 % |
| `accounts/service.py` (cuenta de pruebas sin código) | 99 % |
| `ai/llm/budget.py` (presupuesto de tiempo) | 100 % |
| `ai/llm/gemini.py` (cambio de modelo y corte por tiempo) | 84 % |
| `core/incidents.py` | 100 % |
| `satellite/ndvi.py`, `satellite/service.py` | 100 % |
| `assistant/dialogue.py` | 98 % |
| `assistant/service.py` (ubicación sin IA, proyecto elegido en el contexto) | 97 % |
| `assistant/community.py` | 90 % |
| `registry/importer.py` | 87 % |
| `api/routers/community.py` (texto, ubicación, fotos y notas de voz) | 97 % |

La cobertura más baja corresponde a clientes de servicios externos que no se llaman en las pruebas por diseño (`satellite/providers/gee.py` y `assistant/client.py`, el cliente de Meta que se conserva para la ampliación de WhatsApp).

## 3. Mediciones de requisitos no funcionales

Comando: `uv run bosquevivo medir-rnf --rounds <n> --projects 3`. El asistente se mide con las intenciones del ERS (estado, alertas, ayuda) y dos preguntas libres; sin clave de Gemini las preguntas libres usan la respuesta de respaldo. En producción se midieron, el 05/11/2026, 8 preguntas libres al chat del auditor y 9 mensajes al chat comunitario, y el 19/11/2026, 12 mensajes del chat en línea desde un celular emulado (intenciones del ERS, una pregunta libre, ubicación, foto y una nota de voz hablada), todos con Gemini real.

| Requisito | Meta | Datos simulados (`rnf-fake.json`) | Datos abiertos reales (`rnf-open.json`) | Producción con Gemini real (`rnf-produccion.json`) | Cumple |
|---|---|---|---|---|---|
| 3.3.1 Respuesta del asistente | ≥ 90 % en < 10 s | 100 consultas: p50 0,002 s, p90 0,005 s, máx. 0,009 s, 100 % < 10 s | 20 consultas: p90 0,005 s, 100 % < 10 s | 05/11: 17 consultas, p90 8,5 s, máx. 8,6 s, 100 % < 10 s. 19/11 (`produccion-chat.json`): 12 mensajes, p50 0,3 s, p90 2,6 s, máx. 9,0 s, 100 % < 10 s; foto 4,4 s, nota de voz 2,6 s, ubicación 1,5 s | Sí |
| 3.3.1 Cálculo del índice | < 5 min por polígono | 0,04–0,05 s | 43,7 s, 44,7 s y 62,9 s (MODIS 250 m + Hansen, descarga real) | — | Sí |
| 3.3.3 Determinismo | Mismo índice con los mismos insumos | 99,9/99,9; 100/100; 100/100 | 97,2/97,2; 96,0/96,0; 56,1/56,1 | — | Sí |
| 3.3.3 Incidentes críticos | ≤ 2 al mes | — | — | 1 crítico externo el 19/11/2026: la base de Supabase se pausó por inactividad y la API quedó caída hasta reactivarla (INC-20) | No aplica en esta entrega (plan, 4.3) |
| 3.3.4 Disponibilidad | 95 % en el horario del piloto | — | — | El sitio y la API respondieron en todas las pruebas del 19/11/2026, salvo la caída por la pausa de Supabase (INC-20) | No aplica en esta entrega (plan, 4.3) |

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
| Cuenta de pruebas compartida: entra sin código, no recibe correos, la sesión la muestra | CP-65 | 3 verificaciones aprobadas |
| Sitio sin WhatsApp: `/whatsapp` redirige a `/asistente`, ninguna página lo menciona, el menú lleva al asistente | CP-66 | 3 verificaciones aprobadas |
| Chat en un celular de 390 px: sin desborde, ubicación que registra el proyecto, foto que pide ACEPTO FOTOS y luego se envía, nota de voz grabada con el micrófono, borrado | CP-67, CP-42 | 6 verificaciones aprobadas |

Capturas: `evidencias/capturas/00-invitacion-activada.png` a `11-chat-produccion.png` (`10-chat-celular.png` es el chat en el celular).

Prueba manual adicional (CP-58): `scripts/start.sh` en un clon sin `.env` generó los secretos, la base y los datos de demostración, compiló el sitio y dejó la API (`/health`), el sitio y el chat en línea respondiendo en modo producción.

## 4.1 PostgreSQL y despliegue

| Prueba | Resultado |
|---|---|
| Suite completa contra PostgreSQL 16 (`TEST_DATABASE_URL`) | 360 de 360 aprobadas |
| `migrate-db` de una base SQLite con datos de demostración, cuentas e invitaciones | 233 filas en 21 tablas; registros nuevos sin conflicto de secuencias |
| Entorno solo con el núcleo de dependencias | 274 MB (límite de Vercel: 500 MB) |
| API en modo Vercel (`VERCEL=1`) contra PostgreSQL | `/health`, proyectos, reporte PDF y HTML generados al vuelo, chat comunitario; auditoría rechazada con el mensaje de usar la CLI |
| Producción (Vercel + Supabase) | Sitio https://bosque-vivo-web.vercel.app y API https://bosque-vivo-api.vercel.app; 58 proyectos; `/proyectos` en 1–2 s; reporte PDF, chat en línea con ubicación, fotos y voz, acceso con verificación en dos pasos y documentos legales responden; despliegue automático desde `main` verificado el 19/11/2026 |
| Correo SMTP real (CP-57) | Códigos de verificación, aviso de inicio de sesión y correo de prueba (`POST /api/v1/admin/mail-test`) entregados en Gmail con la plantilla nueva |

## 5. Evaluación de los criterios de aceptación

| Criterio (plan, 4.5.1) | Resultado | Cumple |
|---|---|---|
| 1. 100 % de pruebas automáticas aprobadas y análisis estático sin errores | 360 (SQLite y PostgreSQL) + 100 + 5 aprobadas, 0 errores | Sí |
| 2. Cobertura del backend ≥ 80 % | 89 % | Sí |
| 3. RF01–RF09 con al menos un caso aprobado | 9 de 9 | Sí |
| 4. Casos de prioridad 1 y 2 ejecutados | Todos | Sí |
| 5. 0 incidencias críticas o altas abiertas | 0 abiertas (INC-20 a INC-24 cerradas) | Sí |
| 6. Rendimiento | 100 % < 10 s (también en producción con Gemini real); máximo 62,9 s por polígono | Sí |
| 7. Determinismo | 3 de 3 | Sí |
| 8. Compilación de producción | Correcta | Sí |

**Conclusión.** Se cumplen todos los criterios para dar por completado el plan: los 65 casos especificados están aprobados, en local y en producción, y la prueba con usuarios reales y la medición de disponibilidad durante un piloto quedan fuera de esta entrega (plan, sección 4.3). La calidad de las respuestas libres depende de la disponibilidad de la capa gratuita de Gemini; cuando está saturada, el sistema responde a tiempo con el respaldo. La base gratuita de Supabase se pausa tras una semana sin uso (INC-20); hay que usar el sitio al menos una vez por semana o reactivar la base desde su panel.

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

Producción (chat en línea desde un celular emulado; `PROD_AUDIO` es un WAV con una pregunta hablada, por ejemplo `espeak-ng -v es-419 -w voz.wav "¿cómo está el bosque de mi proyecto?"`):

```bash
PROD_AUDIO=voz.wav PROD_REPORT=docs/plan-de-pruebas/evidencias/produccion-chat.json node docs/plan-de-pruebas/scripts/produccion.cjs
```

Incidentes registrados en producción:

```bash
curl -H "X-Admin-Token: $ADMIN_TOKEN" "https://bosque-vivo-api.vercel.app/api/v1/admin/incidents?days=30"
```
