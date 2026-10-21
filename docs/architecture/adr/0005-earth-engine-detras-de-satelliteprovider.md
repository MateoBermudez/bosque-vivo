# ADR 0005: Google Earth Engine detrás de `SatelliteProvider`

- Estado: aceptada

## Decisión
`SatelliteProvider` define series, pérdida forestal, línea base y miniaturas. `GeeProvider` lo implementa con Sentinel-2 (Cloud Score+), Landsat Collection 2 Nivel 2 y Hansen GFC. `FakeProvider` permite pruebas y demostraciones sin credenciales.

## Consecuencias
- Los identificadores de dataset viven en constantes y se guardan en `audit_run.dataset_versions`.
- Hay que verificar los identificadores vigentes en el catálogo de Earth Engine antes de cada piloto.
