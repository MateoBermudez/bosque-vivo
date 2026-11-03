# Traspaso del proyecto (handoff)

Documento para quien continúe el trabajo en otra sesión. Léelo primero; después sigue el orden de lectura de la sección 3.

## 1. Qué es

Bosque Vivo es el Proyecto Integrador de Ingeniería Informática (ODS 15, Politécnico Colombiano Jaime Isaza Cadavid, 2026-2). Contrasta lo que declaran los proyectos de carbono forestal con lo que se observa desde el satélite y lo explica en lenguaje sencillo con un asistente de IA por WhatsApp y un sitio web para auditores.

Principio central: **la IA interpreta, el sistema mide.** El agente solo cita cifras presentes en la evidencia, hay un validador de fidelidad, un control de lenguaje neutro (nunca «fraude») y una respuesta de respaldo determinista.

Repositorio: https://github.com/MateoBermudez/bosque-vivo (público, rama `main`).

## 2. Reglas del dueño (obligatorias)

- **Ningún commit lleva co-author, firma ni mención de Claude u otra IA. Solo la autoría de Mateo** (`MateoBermudez`). Esto aplica aunque la herramienta sugiera añadir trailers de coautoría.
- **Código sin comentarios.** No dejar `# noqa` ni `# type: ignore`: se corrige el código.
- Git: rama corta por cambio, commits convencionales en piezas lógicas, PR y fusión a `main`. Nunca subir `.env`, `data/`, tokens, llaves SSH ni bases `*.db`.
- `.idea/`, `.vscode/`, `.claude/`, `.mcp.json` y similares están en `.gitignore`.
- Lenguaje neutro en todo el producto: «correspondencia observada», nunca «fraude».
- No enviar a Gemini teléfonos ni nombres; el teléfono solo se guarda como HMAC.

## 3. Orden de lectura

1. `README.md`: decisiones del equipo y ejecución.
2. `docs/planning/PLAN_IMPLEMENTACION.md` y `docs/planning/PLAN_AGENTE_IA.md`.
3. `docs/ers/matriz-de-trazabilidad.md` (requisito → código → pruebas) y `docs/ers/ERS-Bosque-Vivo.pdf`.
4. `docs/architecture/arquitectura.md` y los ADR 0001–0013.
5. `docs/methodology/indice-v0.md` e `indice-v1.md`.
6. `docs/fuentes-de-datos/karnik.md` y `datos-abiertos.md`.
7. `docs/testing/plan-de-pruebas.md` y `resultados.md`.
8. `web/README.md` para el sitio.

## 4. Estado actual

Monorepo (monolito modular) en `main`, con CI en verde en GitHub Actions (jobs de backend, panel y web).

| Parte | Tecnología | Estado |
|---|---|---|
| `backend/` | Python 3.12, uv, FastAPI, SQLAlchemy 2 + SQLite, shapely, agente propio con Gemini | Núcleo completo y probado con proveedores simulados |
| `web/` | Next.js 16, Tailwind v4, MapLibre, zod | Frontend principal (ADR 0013). Modo `mock` o `live` |
| `panel/` | Streamlit | Reemplazado por `web/`; se conserva, se arranca con `STREAMLIT=1` |
| `docs/` | Markdown | Planes, ADR, metodología, pruebas, privacidad, fuentes de datos |

Requisitos implementados: RF01–RF10, RF12, RF13, RF15 y RF17 (ver matriz).

Datos reales: los 55 polígonos de Karnik et al. (2025) para Colombia ya están importados con `bosquevivo import`. El proveedor `open` (MODIS + Hansen) calcula el índice sin cuenta de Earth Engine; hay 33 proyectos de deforestación evitada/IFM calculados. `web/snapshot/` es una copia de solo lectura para publicar el sitio sin servidor.

Índice: v0 se conserva; **v1 es una propuesta pendiente de aprobación del docente** (pesos 35/35/15/15). Con v0 todos los proyectos reales salían «Alta», por eso se propuso v1. Los pesos no están calibrados.

## 5. Cómo ejecutar

```bash
cp .env.example backend/.env
cd backend && uv sync && uv run bosquevivo seed-demo
cd ../web && npm ci
cd .. && scripts/dev.sh
```

- API: http://127.0.0.1:8000 (`/docs`). Sitio: http://localhost:3000. Panel Streamlit (opcional): http://127.0.0.1:8501.
- `scripts/dev.sh` crea `web/.env.local` en modo `live` copiando `ADMIN_TOKEN` del backend. En Windows: `scripts\dev.ps1`.
- Sin credenciales: `SATELLITE_PROVIDER=fake` y los datos de demostración. El chat y WhatsApp necesitan `GEMINI_API_KEY` y `GEMINI_MODEL`; sin ellos la API responde 503 con el motivo.
- `SATELLITE_PROVIDER`: `gee` (Earth Engine), `open` (MODIS + Hansen, sin cuenta), `hansen` (solo pérdida), `fake`.
- Calidad:

```bash
cd backend && uv run ruff format --check . && uv run ruff check . && uv run pyright && uv run pytest
cd web && npm run lint && npm run typecheck && npm test && npm run build
```

Variables de entorno: ver `.env.example`. Las claves reales no están en git y las entrega el dueño: `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_MODEL_LIGHT`, `GEE_PROJECT`, `WHATSAPP_*`, `PHONE_HMAC_KEY`, `ADMIN_TOKEN`. El área de auditores del sitio usa `AUDITOR_ACCESS_CODE` y `SESSION_SECRET`.

## 6. Pendiente

Por orden de valor para la entrega:

1. **Evaluar el agente con Gemini real**: `cd backend && uv run bosquevivo eval`. Hoy solo se probó con un modelo guionizado.
2. **Revisión del docente**: aprobar RF09–RF17 como ampliación del ERS y decidir entre índice v0 y v1. Hacer análisis de sensibilidad de los pesos.
3. **Earth Engine real** (`SATELLITE_PROVIDER=gee`): medir tiempo por polígono y comparar con el proveedor `open`.
4. **WhatsApp real**: configurar Cloud API, túnel (cloudflared/ngrok) y firma del webhook; probar consentimiento y borrado (Ley 1581).
5. **Mediciones de requisitos no funcionales** en la instancia local.
6. **Prueba de comprensión** con 5 personas no técnicas.
7. **RF11** (modelo propio de visión), **RF14** (alertas tempranas), **RF16** (extracción de declaraciones desde PDD): no implementados.
8. Decisión metodológica sobre proyectos de reforestación (ARR), que el índice actual no cubre.
9. Documentación de pruebas: `docs/testing/plan-de-pruebas.md` no está redactado según IEEE 829. Si el docente lo exige, adaptarlo. El formato IEEE 830 (`Formato_ieee830.pdf`) no está en el repo; lo entrega el dueño.
10. `web/`: completar `src/content/team.ts`, definir el canal de contacto humano del aviso de privacidad, imágenes antes/después reales y revisión visual con usuarios.

## 7. Trampas conocidas

- `Formato_ieee830.pdf` y los PDF de la raíz están en `.gitignore`; el ERS vive en `docs/ers/`.
- No pasar el token en la URL del remoto ni dejarlo en `git config`: usar autenticación del entorno.
- El historial de commits fue limpiado de cualquier coautoría; verificar con `git log --format=%B | grep -i -E "co-authored|claude"` antes de cada push (debe dar cero).
- SQLite: hay un trabajador en hilo y escrituras concurrentes; ya se espera el bloqueo de escritura. Para cálculos en lote usar `audit-batch --shard i/n`.
- Los umbrales del índice no se deben ajustar para «producir variedad»: si el índice no distingue, se cambia lo que se mide y se documenta.
