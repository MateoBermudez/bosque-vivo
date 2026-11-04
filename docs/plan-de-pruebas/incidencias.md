# Registro de incidencias

Incidencias encontradas al contrastar el sistema con el ERS (20/10/2026) y al ejecutar el plan de pruebas el 03/11/2026. Severidad: crítica, alta, media, baja. Todas quedaron cerradas y verificadas con la suite completa.

| ID | Caso | Requisito | Descripción | Severidad | Causa | Corrección | Estado |
|---|---|---|---|---|---|---|---|
| INC-01 | CP-02 | RF01 | Un KML con atributos en `Schema`/`SchemaData` se leía sin `project_id` ni fecha, y la fila se rechazaba por falta de identificador | Media | El controlador LIBKML de GDAL expone los atributos de `<Data>` pero no siempre los de `SchemaData` sin esquema resoluble | Se documenta el formato admitido (`ExtendedData/Data`) y se añaden alias de fecha (`begin`, `timestamp`, `registration_date`, `fecha_registro`) | Cerrada |
| INC-02 | CP-30 | RF09 | `/acceso` usaba `Date.now()` durante el prerender y Next mostraba un error en desarrollo | Baja | Con Cache Components la verificación de la sesión debe ejecutarse en tiempo de solicitud | `await connection()` antes de leer la sesión | Cerrada |
| INC-03 | CP-21 | RF07 | En el chat en línea las burbujas de la persona ocupaban todo el ancho | Baja | Faltaba `w-fit` en el párrafo | Estilo corregido | Cerrada |
| INC-04 | CP-25 | RF07 | ALERTAS decía «Todavía no tenemos datos de pérdida» para un proyecto con línea base pero sin pérdida registrada | Media | Se confundía «sin filas de pérdida» con «sin datos» | Si hay línea base y no hay pérdida: «Sin alertas: no se detectó pérdida de bosque» | Cerrada |
| INC-05 | CP-04, CP-05 | RF01 | La importación genérica aceptaba filas sin fecha de registro, reparaba geometrías inválidas en silencio y sobrescribía identificadores existentes | Alta | El importador solo tenía el modo permisivo pensado para la base de Karnik | Modo estricto por defecto en CLI y API, con motivo de rechazo por fila; `--lenient` conserva el comportamiento anterior | Cerrada |
| INC-06 | CP-11 | RF03 | Los valores de NDVI fuera de [−1, 1] se recortaban en lugar de descartarse | Alta | `np.clip` en el cálculo | Se descartan (quedan sin dato) y los puntos inválidos se registran como escena inválida | Cerrada |
| INC-07 | CP-26 | RF07 | Sin `GEMINI_API_KEY` el chat comunitario y WhatsApp fallaban por completo (503) | Alta | El proveedor de IA se construía de forma obligatoria | `UnavailableLLM`: las intenciones del ERS responden sin IA y las preguntas libres usan el respaldo y la ayuda | Cerrada |
| INC-08 | CP-08 | RF02 | El umbral de nubosidad por escena no era configurable (solo existía la máscara por píxel) | Media | Requisito no implementado | `CLOUD_MAX_PERCENT` (20 % por defecto) filtra Sentinel-2 y Landsat y queda en la trazabilidad | Cerrada |
| INC-09 | CP-09 | RF02 | Cuando no había escenas no quedaba registro de la incidencia | Media | Requisito no implementado | Registro de incidentes con origen y severidad (`core/incidents.py`) | Cerrada |
| INC-10 | E2E | Entorno de pruebas | Entre corridas del E2E quedaba vivo el servidor hijo de `next start` y la siguiente corrida usaba el servidor viejo | Baja | `kill` del proceso `npx` no termina su grupo | El script usa `setsid`, termina el grupo de procesos y verifica que los puertos estén libres | Cerrada |
| INC-11 | E2E | Entorno de pruebas | El script E2E contaba el texto de bienvenida del chat como una burbuja de respuesta | Baja | Selector demasiado amplio | Atributo `data-from` en cada burbuja | Cerrada |

## Observaciones que no son defectos

- En desarrollo (`next dev`), tras recargar en caliente el encabezado, React informó un desajuste de hidratación. No se reproduce con la compilación de producción ni en una carga nueva; es propio de la recarga en caliente.
- Las respuestas libres del asistente sin clave de IA usan el texto de respaldo («No puedo responder con seguridad…»). Es el comportamiento esperado (ADR 0009) y queda cubierto por CP-26.
