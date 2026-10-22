# ADR 0013: Next.js para el frontend

- Estado: propuesta (reemplaza a la [0006](0006-streamlit-para-el-panel.md) cuando se apruebe)

## Contexto
El panel de Streamlit cubre lo funcional (índice, serie NDVI, mapa, chat, trazas), pero el equipo definió con Lovable el diseño de un sitio completo (inicio, explorador, detalle, metodología, privacidad) y decidió construirlo en Next.js. Todo sigue corriendo en un solo computador, sin VM ni Docker.

## Decisión
El frontend vive en `web/` (Next.js, App Router, Tailwind v4, TypeScript) y reutiliza los tokens de estilo y la composición del diseño de Lovable. El navegador solo habla con el servidor de Next; este llama a la API de FastAPI.

## Consecuencias
- **Sin CORS:** el backend no necesita habilitarlo, porque las llamadas salen del servidor de Next.
- **El `ADMIN_TOKEN` queda en el servidor de Next.** El chat y las trazas pasan por él; el navegador nunca lo ve. El área de auditores se protege con un código de acceso (`AUDITOR_ACCESS_CODE`).
- **TypeScript entra al equipo**, a cambio de un sitio público completo y mejor control del diseño, la accesibilidad y el mapa.
- **Streamlit deja de ser necesario:** `web/` ya cubre índice, NDVI, mapa, chat, trazas y reporte. `panel/` se conserva por ahora y se retira cuando el equipo apruebe esta decisión.
- **Dos procesos en local** (API y sitio): `scripts/dev` arranca `npm run dev` en lugar de Streamlit. Se requiere Node 22 o superior.
- El frontend valida con zod cada respuesta de la API; un cambio de contrato en el backend se detecta en las pruebas de `web/`.

## Alternativas descartadas
- **Seguir con Streamlit:** más rápido, pero limita el diseño público y la accesibilidad.
- **Mantener la app de Lovable (TanStack Start):** funciona, pero el equipo eligió Next.js como estándar.
