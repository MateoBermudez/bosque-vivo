# Índice de correspondencia v0

> Propuesta a validar con el docente. Implementado en `backend/src/bosquevivo/audit`.

## Qué mide y qué no
Mide la correspondencia entre lo declarado por un proyecto y lo observado desde el satélite en su polígono. No estima contrafactuales ni adicionalidad.

## Entradas
- `T0`: fecha de acreditación. Sale de una declaración revisada (`t0_date`, `crediting_start`, `credit_start_year`) o, en su defecto, del año de inicio del registro.
- Bosque inicial: hectáreas con cobertura arbórea ≥ 30 % en el año 2000 (Hansen GFC).
- Pérdida anual: hectáreas perdidas por año dentro del bosque inicial (Hansen GFC).
- Serie mensual de NDVI por sensor, con fracción de píxeles válidos y escenas por mes. Para el cálculo se usa el sensor con más meses con datos, sin mezclar Landsat y Sentinel-2.

## Componentes

| Componente | Peso | Cálculo |
|---|---|---|
| Permanencia | 50 % | `100 × (1 − pérdida desde T0 / bosque inicial)` |
| Tendencia | 25 % | Pendiente de Theil-Sen del NDVI posterior a T0. Pendiente ≥ 0 da 100; cae linealmente hasta 0 en −0,05 NDVI/año. Si Mann-Kendall no es significativo (α = 0,05), la penalización se reduce a la mitad |
| Estabilidad | 25 % | Mayor caída del promedio móvil de 3 meses de la anomalía estacional posterior a T0. Caída ≤ 0,05 da 100; llega a 0 en 0,30 |

El puntaje es el promedio ponderado de los componentes disponibles. Categorías: Alta ≥ 75, Media ≥ 50, Baja < 50.

## Confianza (aparte del índice)
`0,4 × cobertura + 0,4 × fracción de píxeles válidos + 0,2 × min(1, escenas por mes / 3)`.
Alta ≥ 0,70, media ≥ 0,40, baja en otro caso. Si la fracción de píxeles válidos es menor a 0,15, la confianza se limita a 0,25.

## Resultado "Insuficiente"
Se devuelve sin puntaje cuando ocurre cualquiera de:
- No hay línea base de bosque o falta T0.
- Faltan componentes de tendencia y estabilidad (menos de 12 meses con datos posteriores a T0).
- La confianza es menor a 0,30.
- La fracción de píxeles válidos es menor a 0,15.

Es un resultado legítimo en zonas muy nubosas.

## Alcance por tipo de proyecto
El índice v0 mide la **permanencia de un bosque que ya existía**: parte de la cobertura arbórea del año 2000 (Hansen). Por eso:

| Tipo | Situación |
|---|---|
| Deforestación evitada (AD) y manejo forestal mejorado (IFM) | Soportados |
| **Reforestación (ARR)** | **No soportado en v0.** Un proyecto que planta árboles sobre tierra degradada casi no tenía bosque en 2000, así que no hay línea base y el resultado es «Insuficiente» con el motivo explícito en el texto (no se atribuye a las nubes) |

En la base de Colombia (ver `docs/fuentes-de-datos/karnik.md`) son 22 de 55 proyectos (40 %) de tipo ARR.

**Propuesta para v1, a validar con el docente (no implementada):** para ARR reemplazar *Permanencia* por *Establecimiento de la cobertura*, es decir, cuánto sube el NDVI medio de los últimos 12 meses con datos respecto al promedio de los 3 años previos a T0, normalizado contra una meta que debe fijarse con casos reales. *Tendencia* y *Estabilidad* se mantienen. No se implementó para no introducir umbrales sin validar.

## Ventana de series
Las series satelitales se piden desde **3 años antes de T0** (mínimo el año 2000, inicio de Hansen) hasta hoy, para tener un «antes» y suficientes meses para la estacionalidad sin pedir décadas innecesarias.

## Sensibilidad
Cada reporte incluye el rango del puntaje al mover cada peso ±10 puntos porcentuales y renormalizar.

## Trazabilidad
`audit_run` guarda parámetros completos (`IndexConfig`), versión del índice, SHA del código y versiones de los datasets. Cambiar pesos o umbrales exige subir `version`.

## Limitaciones
- Los NDVI de Landsat y Sentinel-2 no son equivalentes: no se mezclan.
- La pérdida de Hansen no distingue tala de incendio ni de manejo autorizado.
- Un bosque que no cambia puede estar mal declarado o no haber estado en riesgo: el índice no lo evalúa.
- El lenguaje del producto nunca atribuye intención.

## Validación
Conjunto de demostración (`bosquevivo.demo`) con tres casos sintéticos y pruebas golden: intacto (Alta), deforestado (Baja) y nublado (Insuficiente). Falta calibrar con 10 a 15 polígonos reales de comportamiento conocido.
