# Índice sin Earth Engine: datos abiertos (MODIS + Hansen)

## Qué es
`SATELLITE_PROVIDER=open` calcula el **índice completo** de cada proyecto con datos públicos, sin cuenta de Google ni de Earth Engine:

| Componente del índice | Fuente | Cómo se lee |
|---|---|---|
| **Permanencia** (50 %) | Hansen *Global Forest Change* GFC-2024-v1.12: cobertura arbórea del año 2000 y pérdida por año (2001-2024), ~30 m | Ventanas HTTP (`rasterio`) del bucket público de Google Cloud Storage; solo se descarga la parte que cubre el polígono |
| **Tendencia** (25 %) y **Estabilidad** (25 %) | **MODIS MOD13Q1 v061** (NASA): NDVI de 250 m, un compuesto cada 16 días | Catálogo STAC de Microsoft Planetary Computer; ventanas por compuesto, solo píxeles de buena calidad (confiabilidad 0 o 1), promedio mensual |

Referencias: Hansen, M. C., et al. (2013), *Science*, 342, 850-853. Didan, K. (2021). MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061 (MOD13Q1), NASA LP DAAC.

## Proveedores disponibles
| `SATELLITE_PROVIDER` | NDVI | Pérdida de bosque | Miniaturas | Necesita |
|---|---|---|---|---|
| `gee` | Sentinel-2 (10 m) y Landsat (30 m) | Hansen | Sí | Cuenta de Earth Engine (`GEE_PROJECT` + `earthengine authenticate`) |
| **`open`** | **MODIS (250 m)** | Hansen | No | Nada |
| `hansen` | No | Hansen | No | Nada (resultado parcial: solo permanencia) |
| `fake` | Simulado | Simulado | Simuladas | Nada (pruebas y demostración) |

## Cómo se usa
```
cd backend
SATELLITE_PROVIDER=open uv run bosquevivo audit-batch --country Colombia --redo
```
En PowerShell: `$env:SATELLITE_PROVIDER="open"; uv run bosquevivo audit-batch --country Colombia --redo`.

`audit-batch` calcula de menor a mayor área, guarda cada proyecto al terminar, genera su reporte HTML, informa el tiempo y no se detiene si uno falla. Opciones: `--limit N`, `--max-area-ha X`, `--include-arr`, `--redo`, `--shard i/n` (para repartir el trabajo en varios procesos en paralelo, p. ej. 4 procesos con `--shard 1/4` … `--shard 4/4`).

## Tiempos medidos
- Cajambre (70.781 ha): **2 min 54 s** con MODIS + Hansen (199 meses de serie, 2010-2026).
- Solo Hansen: ~8 s para 70.000 ha y ~33 s para 500.000 ha.

## Limitaciones (importante)
- **Resolución:** MODIS es de 250 m; Sentinel-2 y Landsat son de 10 a 30 m. Sirve para tendencias de un territorio, no para parcelas pequeñas ni para detectar claros pequeños. Con Earth Engine el índice es más fino: este proveedor es una alternativa mientras tanto, no un sustituto metodológico.
- **No se mezclan sensores:** el índice usa una sola serie (la de MODIS). Los umbrales de pendiente y caída del índice v0 no se han recalibrado para MODIS.
- **Nubosidad:** en selva húmeda muchos compuestos quedan descartados; la confianza lo refleja (fracción de píxeles válidos).
- **Hansen** mide pérdida de cobertura arbórea, sin distinguir tala, incendio o manejo autorizado; un píxel cuenta como bosque con cobertura >= 30 % en el año 2000.
- **Dependencias externas:** requiere que estén disponibles el bucket de Hansen y Planetary Computer.
- **Reforestación (ARR):** queda fuera del lote por defecto (ver `docs/methodology/indice-v0.md`).
