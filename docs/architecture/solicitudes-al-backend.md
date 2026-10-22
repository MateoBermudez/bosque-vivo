# Solicitudes al backend

Cosas que el frontend necesita o mejoraría con cambios pequeños en `bosque-vivo/backend`. Están ordenadas por
impacto. Todas se probaron contra una copia del backend (commit `9999f11`) con el proveedor de satélite simulado.

## Hechos confirmados (no requieren cambios)
- Las formas de `ProjectOut`, `SeriesOut`, `AuditRunOut`, `ChatOut` y `TraceOut` coinciden con lo que el frontend valida.
- No hace falta CORS: las llamadas salen del servidor de Next.

## Pedidos

> **Hechos desde la primera versión:** polígonos livianos (#3) y el endpoint `GET /api/v1/projects/{id}/declarations` (ficha del proyecto: metodología, desarrollador, periodo de acreditación, origen del contorno).

### 1. Miniaturas antes/después (impacto alto)
Hoy `ver_imagenes` guarda las miniaturas en `data/images`, pero no hay endpoint REST para verlas. El sitio muestra
«Todavía no están disponibles» en modo `live`.
- **Propuesta:** `GET /api/v1/projects/{id}/thumbnail?kind=natural|false_color|ndvi&when=before|after` que devuelva la imagen
  (o 404 si no existe), reutilizando `SatelliteService`.

### 2. Resumen de proyectos en una sola consulta (impacto medio)
El explorador hace 3 llamadas por proyecto (proyecto, geometría y auditoría). Con 20 proyectos son ~60 llamadas por carga.
- **Propuesta:** `GET /api/v1/projects/summary` con `{id, name, country, project_type, start_year, area_ha, score, category,
  confidence_label, geometry}`, o un parámetro `?include=audit,geometry` en `/projects`.

### 3. Polígonos livianos — **resuelto**
`GET /api/v1/projects/{id}/geometry` acepta `?simplify=<grados>` y `?max_parts=<N>`. Los 55 proyectos reales de Colombia pesan 11,5 MB completos (ocho de ellos están formados por cientos o miles de parcelas, uno por 7.258): el explorador pide `simplify=0.005&max_parts=200` y el detalle `simplify=0.0005&max_parts=1000`.

### 4. Fechas con zona horaria (impacto bajo)
`created_at` llega sin zona (`2026-10-21T21:29:33.344399`), que el frontend interpreta como UTC.
- **Propuesta:** emitir siempre `...Z` (datetimes con `tzinfo=UTC`).

### 5. Fecha en las trazas (impacto bajo)
`TraceOut` no trae `created_at`, así que `/trazas` no puede mostrar cuándo ocurrió cada consulta.
- **Propuesta:** agregar `created_at` a `TraceOut`.

### 6. Generar un reporte desde el sitio (impacto bajo)
`GET /audits/{run_id}/report` devuelve 404 si el reporte no se generó, y generarlo es `POST` con token de administración.
- **Propuesta:** el sitio puede ofrecer «Generar reporte» a los auditores llamando a `POST /audits/{id}/report?format=html`.
  No requiere cambios en el backend; solo confirmar que esa es la experiencia deseada.

## Preguntas de producto
- **Contacto humano:** el aviso de privacidad promete «hablar con una persona del equipo». ¿Por qué canal?
- **Retención de trazas:** `/trazas` muestra `query` y `answer` de usuarios de WhatsApp. ¿Se limpian al pedir «BORRAR MIS DATOS»?
  (El commit `9e44bb4` parece cubrir las consultas; conviene confirmar que incluye `agent_run`.)
- **Panel de Streamlit:** ¿se retira `panel/` cuando se adopte este frontend? (ver ADR 0013)
