# Metodología del índice de credibilidad

## Qué mide el índice
El índice mide la correspondencia entre lo que declara un proyecto de carbono forestal y lo que se observa desde el satélite en su polígono. No estima contrafactuales ni adicionalidad: no dice qué habría pasado sin el proyecto.

## Componentes
El índice v0 combina tres componentes: permanencia forestal (50 %), tendencia de vigor (25 %) y estabilidad (25 %). El resultado va de 0 a 100 y se clasifica como Alta, Media, Baja o Insuficiente.

## Permanencia forestal
Es el porcentaje del bosque inicial que sigue en pie desde la fecha de acreditación (T0). Se calcula con la pérdida de cobertura arbórea de Hansen (Global Forest Change) posterior a T0 frente al bosque presente al inicio.

## Tendencia de vigor
Es la pendiente del NDVI posterior a T0, estimada con Theil-Sen y contrastada con Mann-Kendall. Una pendiente positiva o estable no resta puntos; una caída sostenida sí.

## Estabilidad
Detecta caídas abruptas del NDVI después de T0, una vez descontada la estacionalidad propia de cada mes del año.

## Confianza
La confianza se reporta aparte del índice. Depende de cuántos meses tienen datos, qué fracción de píxeles está libre de nubes y cuántas escenas hay por mes. Con nubosidad alta o series cortas la confianza baja.

## Resultado insuficiente
Cuando no hay datos suficientes, el sistema responde Insuficiente en lugar de inventar un puntaje. Es un resultado válido y esperado en zonas muy nubosas como la Amazonía.

## Trazabilidad
Cada cálculo guarda parámetros, versión del índice, versión del código y versiones de los conjuntos de datos, para que cualquier persona pueda reproducirlo.
