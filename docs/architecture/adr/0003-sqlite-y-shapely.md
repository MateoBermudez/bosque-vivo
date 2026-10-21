# ADR 0003: SQLite con shapely en lugar de PostGIS

- Estado: aceptada

## Decisión
SQLite con SQLAlchemy 2. Las geometrías se guardan como GeoJSON y las consultas espaciales usan un índice `STRtree` de shapely en memoria.

## Consecuencias
- Cero instalación y base portable para compartir como semilla.
- Con decenas de polígonos no hay penalización. Si crece a miles, migrar a PostGIS cambia solo `registry.repository`.
