# Fuente de polígonos: base de Karnik et al. (2025)

## Qué es
Base de datos abierta con los contornos de 575 proyectos de carbono forestal en 55 países, recogidos de los registros públicos (433 por *scraping*, 127 georreferenciados a mano). Es la fuente de los polígonos de Bosque Vivo (RF01).

- **Artículo:** Karnik, A., Kilbride, J. B., Goodbody, T. R. H., Ross, R., & Ayrey, E. (2025). An open-access database of nature-based carbon offset project boundaries. *Scientific Data, 12*, 581. https://doi.org/10.1038/s41597-025-04868-2
- **Datos:** Zenodo, v1 (3-jun-2024), https://doi.org/10.5281/zenodo.11459391 · licencia **CC BY 4.0** (hay que citar a los autores).
- No es un censo: el README de los autores advierte que no incluye todos los proyectos ni todos los tipos.

## Cómo cargarla
Archivos (todos del registro de Zenodo; MD5 verificados):

| Archivo | Tamaño | MD5 |
|---|---|---|
| `south_america.gpkg` | 199 897 088 B | `4871b166c0b3e246ce7d6af4df36b28e` |
| `carbon_projects_database_index.csv` | 122 542 B | `106bae839f9b4207006d3c13f9b97957` |
| `README.txt` | 7 969 B | `34888086ca9b4f8da926a1cc47cb5878` |

```
# 1. Descargar a data/raw/ (la carpeta data/ no se sube a git)
# 2. Importar (tarda unos 6 minutos por la reparación de polígonos enormes)
cd backend
uv run bosquevivo import-karnik ../data/raw/karnik_south_america/south_america.gpkg --country Colombia
```
El comando es idempotente: volver a correrlo actualiza en lugar de duplicar.

## Reglas de importación (`backend/src/bosquevivo/registry/karnik.py`)
| Tema | Regla | Por qué |
|---|---|---|
| Polígono | Se audita el **área de contabilidad** si existe; si no, el **área del proyecto** | El área de contabilidad es la usada para calcular los créditos. Si es igual al área del proyecto, la base la deja vacía |
| Puntos | Los proyectos con `Geometry Type = Point` se **omiten** | No hay polígono que auditar (42 en la base mundial) |
| T0 | `Project Start Date` (inicio del periodo de acreditación, mm/dd/yyyy) se guarda como declaración `crediting_start` | Es la fecha desde la que el proyecto se compromete a conservar |
| Geometrías inválidas | Se reparan (`make_valid`) | 54 de las 146 de Sudamérica eran inválidas |
| Polígonos pesados | Se simplifican con la menor tolerancia (0,0001° ≈ 11 m, hasta 0,005°) que baje de 20 000 vértices; la versión guardada lo indica | Hay polígonos de más de **1 millón de vértices**: no caben en una petición a Earth Engine ni se pueden mostrar en el mapa. El área se calcula **antes** de simplificar |
| Tipo de proyecto | AD → *Deforestación evitada (AD)*, ARR → *Reforestación (ARR)*, IFM → *Manejo forestal mejorado (IFM)* | Legible en el sitio, sin perder el código |
| Procedencia | Cada proyecto guarda además la declaración `geometry_source` (qué área se usó y cómo se obtuvo: Official / Georeferenced / Method) | Los contornos georreferenciados a mano son menos fiables que los oficiales |

## Resultado para Colombia (versión v1)
| | |
|---|---|
| Proyectos en la base | 58 |
| Importados | **55** (polígonos) |
| Omitidos por ser solo un punto | 3: `ER31`, `VCS2330`, `VCS2356` |
| Tipo | 32 AD · 22 ARR · 1 IFM |
| Registro | Verra 27 · EcoRegistry 26 · Gold Standard 1 · BioCarbon Registry 1 |
| Inicio de acreditación (T0) | 2002 – 2020 |
| Con área de contabilidad propia | 10 |
| Contorno oficial / georreferenciado / por método | 37 / 16 / 2 |
| Geometrías reparadas / simplificadas | 30 / 17 |
| Tamaño del GeoJSON almacenado | 11,5 MB en total (el mayor, 740 kB) |

## Límites que hay que tener presentes
- **Es una foto de 2024:** los proyectos posteriores no aparecen y los registros pueden haber actualizado sus contornos.
- **Los contornos georreferenciados** (digitalizados desde mapas de los PDD) pueden diferir del real. Los autores midieron una exactitud de 0,98 (IoU), pero no pudieron evaluar los construidos a partir de líneas o de protocolos del desarrollador.
- **No trae lo declarado en cifras** (línea base de deforestación, créditos emitidos): "lo declarado" en Bosque Vivo es que el proyecto está acreditado desde T0 sobre ese polígono.
- La simplificación puede no alcanzar los 20 000 vértices en polígonos formados por muchísimas parcelas pequeñas (por ejemplo, *Regenerating Colombian Coffee Ecosystems* queda en ~30 000); es una cota de mejor esfuerzo.
