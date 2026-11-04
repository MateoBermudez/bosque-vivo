# Informe de resultados de pruebas

Ejecución del [plan de pruebas](plan-de-pruebas.md) sobre la rama de trabajo que se fusionó a `main` el 03/11/2026. Entorno: Linux, Python 3.12, Node 22, Chromium con Playwright; base SQLite en memoria (pruebas automáticas) y bases temporales (E2E y mediciones).

## 1. Resumen

| Indicador | Resultado |
|---|---|
| Casos especificados | 62 |
| Casos aprobados | 56 (90 %) |
| Casos fallidos | 0 |
| Casos bloqueados por dependencias externas | 6 (CP-29, CP-46, CP-49, CP-50, el envío SMTP real de CP-57 y el despliegue real de CP-62) |
| Requisitos funcionales RF01–RF09 con casos aprobados | 9 de 9 (100 %) |
| Pruebas automáticas del backend | 330 aprobadas, 0 fallidas, tanto en SQLite como en PostgreSQL 16 |
| Cobertura de líneas del backend | 88 % (5.438 sentencias) |
| Pruebas del sitio (Vitest) | 94 aprobadas en 10 archivos |
| Pruebas del panel | 5 aprobadas |
| Verificaciones E2E en navegador | 30 de 30 aprobadas |
| Análisis estático | `ruff` y `pyright`: 0 errores; `eslint` y `tsc`: 0 errores |
| Compilación de producción del sitio | Correcta |
| Incidencias registradas | 14 (todas cerradas; ver [`incidencias.md`](incidencias.md)) |

## 2. Resultados por suite

| Suite | Comando | Resultado | Evidencia |
|---|---|---|---|
| Backend: estilo | `uv run ruff check . && uv run ruff format --check .` | Sin errores, 158 archivos con formato | `evidencias/backend-ruff.txt` |
| Backend: tipos | `uv run pyright` | 0 errores | `evidencias/backend-pyright.txt` |
| Backend: pruebas y cobertura | `uv run pytest --cov=bosquevivo --junitxml=...` | 330 aprobadas en 28 s, cobertura 88 %; las mismas 330 en PostgreSQL 16 | `evidencias/backend-pytest.txt`, `backend-junit.xml`, `backend-postgres-junit.xml` |
| Sitio: estilo | `npm run lint` | Sin errores | `evidencias/web-lint.txt` |
| Sitio: pruebas | `npx vitest run` | 94 aprobadas | `evidencias/web-vitest.txt`, `web-junit.xml` |
| Sitio: compilación | `npm run build` | Correcta | `evidencias/web-build.txt` |
| Panel | `uv run pytest` | 5 aprobadas | — |
| E2E | `docs/plan-de-pruebas/scripts/ejecutar-e2e.sh` | 30 de 30 | `evidencias/e2e-salida.txt`, `e2e-resultados.json`, `evidencias/capturas/` |

### Cobertura de los módulos nuevos o modificados

| Módulo | Cobertura |
|---|---|
| `accounts/service.py` (RF09, 2FA, avisos, invitaciones) | 98 % |
| `accounts/mailer.py`, `accounts/templates.py` (SMTP) | 98 % |
| `setup.py` (configuración automática) | 99 % |
| `api/routers/auth.py` | 91 % |
| `accounts/passwords.py` | 95 % |
| `core/incidents.py` | 100 % |
| `satellite/ndvi.py` | 100 % |
| `satellite/service.py` | 100 % |
| `assistant/dialogue.py` | 98 % |
| `assistant/service.py` | 95 % |
| `assistant/community.py` | 90 % |
| `registry/importer.py` | 87 % |
| `api/routers/community.py` | 100 % |

La cobertura más baja corresponde a clientes de servicios externos que no se llaman en las pruebas por diseño (`satellite/providers/gee.py`, `assistant/client.py` de Meta y `ai/llm/gemini.py`).

## 3. Mediciones de requisitos no funcionales

Comando: `uv run bosquevivo medir-rnf --rounds <n> --projects 3`. El asistente se mide con las intenciones del ERS (estado, alertas, ayuda) y dos preguntas libres; sin clave de Gemini las preguntas libres usan la respuesta de respaldo.

| Requisito | Meta | Datos simulados (`rnf-fake.json`) | Datos abiertos reales (`rnf-open.json`) | Cumple |
|---|---|---|---|---|
| 3.3.1 Respuesta del asistente | ≥ 90 % en < 10 s | 100 consultas: p50 0,002 s, p90 0,005 s, máx. 0,009 s, 100 % < 10 s | 20 consultas: p90 0,005 s, 100 % < 10 s | Sí (repetir con Gemini real) |
| 3.3.1 Cálculo del índice | < 5 min por polígono | 0,04–0,05 s | 43,7 s, 44,7 s y 62,9 s (MODIS 250 m + Hansen, descarga real) | Sí |
| 3.3.3 Determinismo | Mismo índice con los mismos insumos | 99,9/99,9; 100/100; 100/100 | 97,2/97,2; 96,0/96,0; 56,1/56,1 | Sí |
| 3.3.3 Incidentes críticos | ≤ 2 al mes | — | — | Se mide en el piloto (CP-46) |
| 3.3.4 Disponibilidad | 95 % en el horario del piloto | — | — | Se mide en el piloto (CP-46) |

## 4. Pruebas de extremo a extremo

`scripts/ejecutar-e2e.sh` crea una base temporal con los proyectos de demostración, invita una cuenta de auditor (`bosquevivo user-invite`), activa la verificación en dos pasos con el buzón local (`AUTH_TWO_FACTOR=on`), levanta la API y el sitio compilado, y recorre en Chromium:

| Flujo | Casos | Resultado |
|---|---|---|
| Invitación: correo con enlace, bienvenida, primera contraseña | CP-56 | 3 verificaciones aprobadas |
| Recuperación de contraseña (RF09): acceso restringido, credenciales inválidas, mensaje genérico, enlace por correo, token inválido, contraseñas distintas y débiles, actualización, enlace reutilizado | CP-30 a CP-36 | 10 verificaciones aprobadas |
| Verificación en dos pasos y avisos: código por correo, código incorrecto, reenvío, entrada con la contraseña nueva, sesión con el correo, aviso de inicio de sesión, aviso de cambio de contraseña, correos con HTML | CP-37, CP-53 a CP-55 | 8 verificaciones aprobadas |
| Chat en línea (RF07, RF08, Ley 1581): saludo y aviso, consentimiento, ayuda, registro del proyecto, estado, lenguaje sencillo, alertas, consulta no reconocida, borrado | CP-21 a CP-28, CP-42 | 9 verificaciones aprobadas |

Capturas: `evidencias/capturas/00-invitacion-activada.png` a `08-codigo-2fa.png`.

Prueba manual adicional (CP-58): `scripts/start.sh` en un clon sin `.env` generó los secretos, la base y los datos de demostración, compiló el sitio y dejó la API (`/health`), el sitio y el chat en línea respondiendo en modo producción.

## 4.1 PostgreSQL y despliegue (versión 1.2)

| Prueba | Resultado |
|---|---|
| Suite completa contra PostgreSQL 16 (`TEST_DATABASE_URL`) | 330 de 330 aprobadas |
| `migrate-db` de una base SQLite con datos de demostración, cuentas e invitaciones | 233 filas en 21 tablas; registros nuevos sin conflicto de secuencias |
| Entorno solo con el núcleo de dependencias | 274 MB (límite de Vercel: 500 MB) |
| API en modo Vercel (`VERCEL=1`) contra PostgreSQL | `/health`, proyectos, reporte PDF y HTML generados al vuelo, chat comunitario; auditoría rechazada con el mensaje de usar la CLI |

## 5. Evaluación de los criterios de aceptación

| Criterio (plan, 4.5.1) | Resultado | Cumple |
|---|---|---|
| 1. 100 % de pruebas automáticas aprobadas y análisis estático sin errores | 330 (SQLite y PostgreSQL) + 94 + 5 aprobadas, 0 errores | Sí |
| 2. Cobertura del backend ≥ 80 % | 88 % | Sí |
| 3. RF01–RF09 con al menos un caso aprobado | 9 de 9 | Sí |
| 4. Casos de prioridad 1 y 2 ejecutados | Todos, salvo CP-29 (usuarios del piloto) | Sí, con la excepción prevista |
| 5. 0 incidencias críticas o altas abiertas | 0 abiertas | Sí |
| 6. Rendimiento | 100 % < 10 s; máximo 62,9 s por polígono | Sí |
| 7. Determinismo | 3 de 3 | Sí |
| 8. Compilación de producción | Correcta | Sí |

**Conclusión.** Se cumplen los criterios para dar por completado el plan en esta etapa. Quedan cinco casos o partes bloqueados por dependencias externas (credenciales de Meta, de Google AI Studio y de correo SMTP, y usuarios del piloto); tienen guía de ejecución en [`docs/guias`](../guias) y en este plan, y no afectan los requisitos funcionales comprometidos, que se verificaron sin ellos.

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
