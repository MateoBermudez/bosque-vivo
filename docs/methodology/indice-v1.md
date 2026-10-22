# Índice de credibilidad v1 (propuesta)

Estado: **propuesta pendiente de aprobación del docente**. El índice [v0](indice-v0.md) se conserva sin
cambios: cada auditoría guarda la versión con la que se calculó y las corridas v0 siguen en la base para
comparar.

## Por qué existe

Con v0, los 27 proyectos colombianos de deforestación evitada calculados quedaron entre 92,5 y 100
(todos «Alta»). No era un error de cálculo: la permanencia es el porcentaje del bosque inicial que sigue en
pie, y en territorios de decenas de miles de hectáreas incluso una pérdida real se vuelve una fracción
pequeña; el NDVI de 250 m sobre áreas tan grandes casi no se mueve. El índice no distinguía.

Los umbrales **no** se ajustaron para producir variedad. Se cambió lo que se mide.

## Qué cambia

| Componente | v0 | v1 |
|---|---|---|
| Permanencia | 50 %. Bosque aún en pie (%) | 35 %. **Pérdida anual** desde T0 como % del bosque inicial: 0 % → 100; 1 %/año → 0 |
| Evolución de la pérdida | no existe | 35 %. Cociente entre la pérdida anual media **después** de T0 y la de **antes** (2001 → T0): ≤ 1 → 100; 2 → 50; ≥ 3 → 0 |
| Tendencia (NDVI) | 25 % | 15 %, sin cambios en el método |
| Estabilidad (NDVI) | 25 % | 15 %, sin cambios en el método |

Reglas de la evolución de la pérdida:

- Necesita al menos 3 años de referencia antes de T0; si no, el componente queda sin puntaje y su peso se
  reparte entre los demás.
- Si la pérdida anual es despreciable (< 0,01 % del bosque inicial) antes y después, puntúa 100.
- Si antes de T0 no hubo pérdida y después sí, no hay con qué comparar: sin puntaje (no se inventa un cociente).
- Años sin registro de pérdida en Hansen cuentan como 0 ha. Los datos llegan hasta 2024 (`loss_last_year`).

Categorías y confianza no cambian (Alta ≥ 75, Media ≥ 50, Baja < 50).

## Límites que hay que decir siempre

- **No es causalidad.** Compara el polígono consigo mismo; no estima qué habría pasado sin el proyecto. Si la
  deforestación subió en toda la región, el cociente sube aunque el proyecto no tenga la culpa. El texto
  habla de «evolución observada», nunca de incumplimiento.
- Los pesos (35/35/15/15), el 1 %/año y el cociente 1–3 son una propuesta razonada, no calibrada con casos
  validados. Hay que revisarlos con el docente y hacer un análisis de sensibilidad antes de usarlos como
  criterio.
- Sigue sin cubrir reforestación (ARR).

## Resultado sobre los proyectos reales calculados (Colombia, 33 AD/IFM)

27 «Alta» y 6 «Media»; rango 58,5–99,8 (v0: 92,5–100). Los más bajos son los de pérdida creciente tras T0
(p. ej. Carmen del Darién, 8 veces más hectáreas por año que antes).

## Cómo reproducirlo

```bash
cd backend
uv run bosquevivo recompute --index-version v1   # usa los datos ya guardados; no vuelve al satélite
uv run bosquevivo audit-batch --country Colombia --redo --index-version v1   # con satélite
```

`INDEX_VERSION` (por defecto `v1`) define la versión de las auditorías nuevas.
