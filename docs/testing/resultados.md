# Resultados de pruebas

| Fecha | Suite | Resultado | Notas |
|---|---|---|---|
| 2026-10-20 | `pytest` backend | 159 aprobadas | Modelo guionizado y proveedor de satélite simulado |
| 2026-10-21 | `pytest` backend (rama `feat/karnik-import`) | 184 aprobadas | Incluye 25 pruebas nuevas: importador de Karnik, simplificación de polígonos, ventana de series según T0, texto del resultado, geometría ligera |
| 2026-10-21 | Importación real de Karnik (Colombia) | 55 proyectos, 3 puntos omitidos, 10 con área de contabilidad | Verificada la integridad de SQLite, los T0 y los tamaños; ver `docs/fuentes-de-datos/karnik.md` |
| 2026-10-20 | `pytest` panel | 5 aprobadas | |
| 2026-10-20 | Humo de extremo a extremo | Aprobado | API, trabajador, reporte HTML y panel con datos de demostración |

## Pendiente
- Evaluación del agente con Gemini real (`bosquevivo eval`).
- Mediciones de NFR en la instancia local.
- Validación del índice con polígonos reales y Earth Engine real (los 55 polígonos ya están cargados; faltan las series satelitales y medir el tiempo por polígono).
- Decisión metodológica sobre los proyectos de reforestación (ARR): ver `docs/methodology/indice-v0.md`.
- Prueba de comprensión con 5 personas no técnicas.
