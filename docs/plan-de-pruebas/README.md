# Plan de pruebas (IEEE 829)

Objetivo específico 4 del proyecto: probar Bosque Vivo con un plan que verifique el cumplimiento de los requisitos del ERS (IEEE 830, versión del 20/10/2026). Sigue la plantilla «Formato_ieee829» del Politécnico.

| Documento | Contenido |
|---|---|
| [`plan-de-pruebas.md`](plan-de-pruebas.md) | El plan: historial, información del proyecto, aprobaciones, alcance y estrategia, criterios de aceptación, entregables, recursos, organización, riesgos, referencias y glosario |
| [`casos-de-prueba.md`](casos-de-prueba.md) | 52 casos de prueba (CP-01 a CP-52) con requisito, pasos, resultado esperado, prueba automática y resultado |
| [`informe-de-resultados.md`](informe-de-resultados.md) | Resultados de la ejecución, cobertura, mediciones de rendimiento y determinismo, E2E y evaluación de los criterios de aceptación |
| [`incidencias.md`](incidencias.md) | Incidencias encontradas y su corrección |
| [`Plan_de_Pruebas_Bosque_Vivo.docx`](Plan_de_Pruebas_Bosque_Vivo.docx) | Los cuatro documentos anteriores en un solo archivo de Word para entregar |
| [`evidencias/`](evidencias) | Reportes JUnit, salidas de las herramientas, mediciones (`rnf-*.json`), resultado E2E y capturas |
| [`scripts/`](scripts) | `ejecutar-e2e.sh` y `e2e.cjs` (Playwright), `disponibilidad.sh` (piloto) |

Resultado del 03/11/2026: 48 de 52 casos aprobados, 0 fallidos y 4 bloqueados por credenciales o usuarios del piloto (CP-29, CP-46, CP-49, CP-50).

Regenerar el `.docx` después de editar los Markdown:

```bash
cd docs/plan-de-pruebas
pandoc plan-de-pruebas.md casos-de-prueba.md informe-de-resultados.md incidencias.md \
  --toc --toc-depth=2 -M toc-title="Tabla de contenido" -o Plan_de_Pruebas_Bosque_Vivo.docx
```
