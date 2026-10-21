# Bosque Vivo · Frontend (`web/`)

Sitio web de Bosque Vivo (Next.js). Muestra proyectos de carbono forestal con su índice de credibilidad,
la serie NDVI, la pérdida de bosque y el reporte, e incluye el chat del auditor y las trazas del agente.

El diseño parte del código que generó Lovable (`EmmanuelArangoV/screenshot-exact-match`): se conservaron sus
**tokens de estilo, tipografía y composición**, y se rehízo la base técnica sobre Next.js.

## Decisiones

| Tema | Decisión |
|---|---|
| **Framework** | Next.js 16 (App Router) con Cache Components. Reemplaza al panel de Streamlit (ver [ADR 0013](../docs/architecture/adr/0013-nextjs-para-el-frontend.md)). |
| **Estilos** | Tailwind CSS v4 con los mismos tokens de Lovable (`src/app/globals.css`), fuente Manrope, utilidades `card-soft`, `glass`, `btn-*`. |
| **Datos** | Capa única en `src/lib/api`. Dos orígenes con el mismo contrato: `mock` (datos de ejemplo) y `live` (API real). |
| **Validación** | Las respuestas del backend se validan con zod (`src/lib/api/schema.ts`). Si el backend cambia, el sitio falla con un mensaje claro. |
| **Backend por detrás** | El navegador nunca habla con el backend: lo hace el servidor de Next. Por eso **no hace falta CORS** y el `ADMIN_TOKEN` nunca llega al navegador. |
| **Mapa** | MapLibre GL con polígonos reales coloreados por categoría. Mosaicos CARTO (configurable). |
| **Todo local** | Igual que el resto del proyecto: sin VM ni Docker. Corre con `npm`. |

## Ejecutar

Requisitos: Node 22 o superior (probado con 24) y npm.

```bash
npm install
cp .env.example .env.local     # en PowerShell: Copy-Item .env.example .env.local
npm run dev                    # http://localhost:3000
```

Sin configurar nada arranca en modo `mock`: no necesita el backend.

### Con la API real

En `.env.local`:

```
BV_DATA_SOURCE=live
BACKEND_URL=http://127.0.0.1:8000
ADMIN_TOKEN=<el mismo ADMIN_TOKEN del backend>
```

El aviso «datos ilustrativos» sale solo cuando hay proyectos del registro `demo` (la base de demostración de `bosquevivo seed-demo`); `BV_SAMPLE_NOTICE=1` lo fuerza.

y levanta el backend (`cd backend && uv run uvicorn bosquevivo.api.app:app`). Con `scripts/dev` (en la raíz del repo) todo esto se hace solo: arranca la API y el sitio, y crea `web/.env.local` copiando el `ADMIN_TOKEN` de `backend/.env`.

### Área de auditores

El chat y las trazas consumen la cuota de IA y las trazas muestran preguntas de usuarios, así que están protegidas:

- Define `AUDITOR_ACCESS_CODE` y `SESSION_SECRET` (`openssl rand -hex 32`). Se inicia sesión en `/acceso`.
- Sin definirlas, el área queda **abierta en desarrollo** y **bloqueada en producción**.

## Rutas

| Ruta | Contenido |
|---|---|
| `/` | Inicio: problema, cómo funciona, asistente, qué mide y qué no |
| `/proyectos` | Explorador: mapa + lista con filtros |
| `/proyectos/[id]` | Detalle: índice, componentes, NDVI, pérdida, antes/después, declarado vs observado, reproducibilidad |
| `/whatsapp` | Cómo usar el asistente (con código QR si hay número configurado) |
| `/metodologia` | Índice, confianza, limitaciones, glosario, preguntas frecuentes, normativa |
| `/privacidad` | Aviso de privacidad (Ley 1581) |
| `/acerca` | Objetivos, alcance, referencias |
| `/chat` · `/trazas` | Auditores: chat con el agente y trazas (requieren acceso) |
| `/informe/[runId]` | Descarga del reporte (lo entrega el servidor de Next, no el backend) |

## Estructura

```
src/
├─ app/                 rutas (App Router)
├─ components/          layout, common, home, projects, chat, ui
├─ content/             textos de apoyo (glosario, preguntas frecuentes, normativa, equipo)
├─ lib/
│  ├─ api/              schema (zod), backend (cliente real), mock, index (selección)
│  ├─ auth/             sesión firmada del área de auditores
│  └─ domain.ts         pesos y umbrales del índice, lectura de componentes
└─ proxy.ts             protege /chat, /trazas y /api/chat
```

## Calidad

```bash
npm run lint
npm run typecheck
npm test            # vitest
npm run build
```

Las pruebas incluyen un **contrato**: los datos de ejemplo deben cumplir el mismo esquema que la API real,
y el cliente del backend se prueba con respuestas simuladas (404, errores, formato inesperado, token).

## Pendiente

- Equipo: completar `src/content/team.ts` para que aparezca la sección en `/acerca`.
- Contacto humano del aviso de privacidad ("hablar con una persona del equipo"): falta definir el canal.
- Imágenes antes/después reales y otras mejoras que dependen del backend: ver [solicitudes al backend](../docs/architecture/solicitudes-al-backend.md).
- Revisión visual en navegador y pruebas con usuarios no técnicos.
