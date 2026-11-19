# Metodología del índice de credibilidad

## Qué mide el índice
El índice mide la correspondencia entre lo que declara un proyecto de carbono forestal y lo que se observa desde el satélite en su polígono. No estima contrafactuales ni adicionalidad: no dice qué habría pasado sin el proyecto.

## Componentes
El índice v1, una propuesta en validación que es la versión en uso, combina cuatro componentes: permanencia forestal (35 %), evolución de la pérdida (35 %), tendencia de vigor (15 %) y estabilidad (15 %). El resultado va de 0 a 100 y se clasifica como Alta, Media, Baja o Insuficiente. La versión anterior, v0, usaba tres componentes (permanencia 50 %, tendencia 25 % y estabilidad 25 %) y se conserva para comparar.

## Permanencia forestal
En el índice v1 mide cuánto bosque se pierde cada año desde la fecha de acreditación (T0), como porcentaje del bosque que había al inicio: sin pérdida da 100 y una pérdida de 1 % del bosque inicial por año da 0. Se calcula con la pérdida de cobertura arbórea de Hansen (Global Forest Change). El porcentaje de bosque que sigue en pie desde T0 se muestra como dato de apoyo y era el valor de este componente en el índice v0.

## Evolución de la pérdida
Compara la pérdida anual de bosque después de T0 con la de los años anteriores en el mismo polígono. Si se mantiene o baja, da 100; si se duplica, 50; si se triplica o más, 0. Es una comparación del polígono consigo mismo: no descarta que el cambio se deba a causas de toda la región y no demuestra que el proyecto sea responsable. Si antes de T0 casi no había pérdida y después tampoco, el resultado es 100. Si antes no había pérdida y después sí, no hay con qué comparar y el componente queda sin puntaje.

## Tendencia de vigor
Es la pendiente del NDVI posterior a T0, estimada con Theil-Sen y contrastada con Mann-Kendall. Una pendiente positiva o estable no resta puntos; una caída sostenida sí.

## Estabilidad
Detecta caídas abruptas del NDVI después de T0, una vez descontada la estacionalidad propia de cada mes del año.

## Confianza
La confianza se reporta aparte del índice. Depende de cuántos meses tienen datos, qué fracción de píxeles está libre de nubes y cuántas escenas hay por mes. Con nubosidad alta o series cortas la confianza baja.

## Qué no mide el índice
No estima qué habría pasado sin el proyecto, no evalúa si las reducciones de emisiones son adicionales, no distingue tala de incendio ni de manejo autorizado, y todavía no cubre los proyectos de reforestación porque no tienen bosque inicial con el que comparar. El sistema no registra el departamento ni el municipio de los proyectos, solo el país.

## Resultado insuficiente
Cuando no hay datos suficientes, el sistema responde Insuficiente en lugar de inventar un puntaje. Es un resultado válido y esperado en zonas muy nubosas como la Amazonía.

## Trazabilidad
Cada cálculo guarda parámetros, versión del índice, versión del código y versiones de los conjuntos de datos, para que cualquier persona pueda reproducirlo.
