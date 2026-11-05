# Plan de pruebas (IEEE 829)

Objetivo específico 4 del proyecto: probar Bosque Vivo con un plan que verifique el cumplimiento de los requisitos del ERS (IEEE 830, revisión 1.1 del 05/11/2026, en [`docs/ers`](../ers)). Sigue la plantilla «Formato_ieee829» del Politécnico.

| Documento | Contenido |
|---|---|
| [`plan-de-pruebas.md`](plan-de-pruebas.md) | El plan: historial, información del proyecto, aprobaciones, alcance y estrategia, criterios de aceptación, entregables, recursos, organización, riesgos, referencias y glosario |
| [`casos-de-prueba.md`](casos-de-prueba.md) | 62 casos de prueba (CP-01 a CP-62) con requisito, pasos, resultado esperado, prueba automática y resultado |
| [`informe-de-resultados.md`](informe-de-resultados.md) | Resultados de la ejecución, cobertura, mediciones de rendimiento y determinismo, E2E y evaluación de los criterios de aceptación |
| [`incidencias.md`](incidencias.md) | Incidencias encontradas y su corrección |
| [`Plan_de_Pruebas_Bosque_Vivo.docx`](Plan_de_Pruebas_Bosque_Vivo.docx) · [`.pdf`](Plan_de_Pruebas_Bosque_Vivo.pdf) | Los cuatro documentos anteriores en un solo archivo para entregar (Word y PDF) |
| [`evidencias/`](evidencias) | Reportes JUnit, salidas de las herramientas, mediciones (`rnf-*.json`), resultado E2E y capturas |
| [`scripts/`](scripts) | `ejecutar-e2e.sh` y `e2e.cjs` (Playwright), `disponibilidad.sh` (piloto), `generar-documento.sh` (Word y PDF) |

Resultado al 05/11/2026: 58 de 62 casos aprobados, 0 fallidos y 4 pendientes del piloto o de WhatsApp (CP-29, CP-46, CP-49 y la evaluación formal de CP-50). El sistema está desplegado en https://bosque-vivo-web.vercel.app con correo SMTP y Gemini activos.

Regenerar el `.docx` y el `.pdf` después de editar los Markdown (requiere pandoc y Playwright):

```bash
bash docs/plan-de-pruebas/scripts/generar-documento.sh
```

Al abrir el `.docx`, Word ofrece actualizar los campos: acepte para que se llene la tabla de contenido.
