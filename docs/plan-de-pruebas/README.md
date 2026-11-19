# Plan de pruebas (IEEE 829)

Objetivo específico 4 del proyecto: probar Bosque Vivo con un plan que verifique el cumplimiento de los requisitos del ERS (IEEE 830, revisión 1.2 del 19/11/2026, en [`docs/ers`](../ers)). Sigue la plantilla «Formato_ieee829» del Politécnico.

| Documento | Contenido |
|---|---|
| [`plan-de-pruebas.md`](plan-de-pruebas.md) | El plan: historial, información del proyecto, aprobaciones, alcance y estrategia, criterios de aceptación, entregables, recursos, organización, riesgos, referencias y glosario |
| [`casos-de-prueba.md`](casos-de-prueba.md) | 67 casos de prueba (CP-01 a CP-67) con requisito, pasos, resultado esperado, prueba automática y resultado |
| [`informe-de-resultados.md`](informe-de-resultados.md) | Resultados de la ejecución, cobertura, mediciones de rendimiento y determinismo, E2E y evaluación de los criterios de aceptación |
| [`incidencias.md`](incidencias.md) | Incidencias encontradas y su corrección |
| [`Formato_ieee829.docx`](Formato_ieee829.docx) · [`.pdf`](Formato_ieee829.pdf) | Documento para entregar (Word y PDF) con el formato «Formato_ieee829» del Drive: el plan y, como anexos, los casos de prueba, el informe de resultados y las incidencias |
| [`evidencias/`](evidencias) | Reportes JUnit (SQLite y PostgreSQL), salidas de las herramientas, mediciones (`rnf-*.json`, incluidas `rnf-produccion.json` y `produccion-chat.json` con Gemini real), resultado E2E y capturas |
| [`scripts/`](scripts) | `ejecutar-e2e.sh` y `e2e.cjs` (Playwright), `produccion.cjs` (chat en línea en producción), `disponibilidad.sh` (piloto), `generar-documento.sh` y `generar_documento.py` (Word y PDF sobre la plantilla) |

Resultado de la ejecución completa del 19/11/2026 (plan versión 1.4): 65 de 67 casos aprobados, 0 fallidos y 2 bloqueados por el piloto (CP-29 y CP-46); de CP-50 queda pendiente solo la evaluación formal de 20 casos. El sistema está desplegado en https://bosque-vivo-web.vercel.app con correo SMTP y Gemini activos, ofrece el asistente por el chat en línea (`/asistente`) con texto, ubicación, fotos y notas de voz, y publica términos y condiciones, política de privacidad y uso de datos.

Regenerar el `.docx` y el `.pdf` después de editar los Markdown (requiere pandoc, LibreOffice y uv). El documento se arma sobre la plantilla «Formato_ieee829» del Drive (`plantilla/Formato_ieee829.docx`): portada, tabla de contenido, encabezado y pie del Politécnico, títulos y tablas con su formato; los casos de prueba, el informe de resultados y las incidencias van como anexos A, B y C:

```bash
bash docs/plan-de-pruebas/scripts/generar-documento.sh
```

La tabla de contenido ya trae los números de página; si Word ofrece actualizar los campos al abrirlo, se puede aceptar.
