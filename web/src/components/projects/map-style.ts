import type { StyleSpecification } from "maplibre-gl";

import type { ProjectGeometry } from "@/lib/api/schema";

// Imágenes satelitales de Esri (no piden clave). CARTO empezó a exigir una clave API.
const DEFAULT_TILES = [
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
];
const DEFAULT_ATTRIBUTION = "Imágenes © Esri, Maxar, Earthstar Geographics y la comunidad GIS";
const TILES = process.env.NEXT_PUBLIC_MAP_TILES_URL ? [process.env.NEXT_PUBLIC_MAP_TILES_URL] : DEFAULT_TILES;
const FOREST = "#1f3a28";

/** El worker se copia a /public (scripts/copy-maplibre-worker.mjs): con Turbopack la ruta que
 * MapLibre calcula sola no existe y falla con «Worker failed to load». */
export const WORKER_URL = "/vendor/maplibre/maplibre-gl-worker.mjs";

// Si no hay conexión a los mosaicos, los polígonos se siguen viendo sobre el fondo verde.
export const MAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    base: {
      type: "raster",
      tiles: TILES,
      tileSize: 256,
      maxzoom: 17,
      attribution: process.env.NEXT_PUBLIC_MAP_ATTRIBUTION ?? DEFAULT_ATTRIBUTION,
    },
  },
  layers: [
    { id: "fondo", type: "background", paint: { "background-color": FOREST } },
    { id: "base", type: "raster", source: "base", paint: { "raster-opacity": 1 } },
  ],
};

type Bounds = [[number, number], [number, number]];

/** Rectángulo que contiene todos los polígonos, o `null` si no hay ninguno. */
export function boundsOf(geometries: ProjectGeometry["geometry"][]): Bounds | null {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  const visit = (position: number[]) => {
    const [x, y] = position;
    if (x === undefined || y === undefined) return;
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  };
  for (const geometry of geometries) {
    const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
    for (const polygon of polygons) for (const ring of polygon) ring.forEach(visit);
  }
  return Number.isFinite(minX)
    ? [
        [minX, minY],
        [maxX, maxY],
      ]
    : null;
}
