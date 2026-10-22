"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useMemo, useRef, useState } from "react";

import type { Category, ProjectGeometry } from "@/lib/api/schema";
import { CATEGORIES } from "@/lib/api/schema";
import { categoryHex } from "@/lib/domain";

import { MAP_STYLE, WORKER_URL, boundsOf } from "./map-style";

export interface MapItem {
  id: number;
  name: string;
  country: string | null;
  /** `null` cuando el proyecto todavía no tiene auditoría. */
  category: Category | null;
  geometry: ProjectGeometry["geometry"];
}

interface ProjectMapProps {
  items: MapItem[];
  highlightId: number | null;
  onHighlight: (id: number | null) => void;
  onSelect: (id: number) => void;
}

const SOURCE_ID = "projects";

function toCollection(items: MapItem[]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: items.map((item) => ({
      type: "Feature",
      geometry: item.geometry as GeoJSON.Geometry,
      properties: {
        id: item.id,
        name: item.name,
        color: categoryHex[item.category ?? "Insuficiente"],
      },
    })),
  };
}

export function ProjectMap({ items, highlightId, onHighlight, onSelect }: ProjectMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const handlers = useRef({ onHighlight, onSelect });
  const highlighted = useRef<number | null>(null);
  const [ready, setReady] = useState(false);
  const [hoverId, setHoverId] = useState<number | null>(null);
  const [failed, setFailed] = useState(false);
  const collection = useMemo(() => toCollection(items), [items]);

  useEffect(() => {
    handlers.current = { onHighlight, onSelect };
  }, [onHighlight, onSelect]);

  // Crea el mapa una sola vez (MapLibre necesita el navegador, por eso se importa aquí).
  useEffect(() => {
    let cancelled = false;
    let map: MapLibreMap | null = null;

    import("maplibre-gl")
      .then((maplibre) => {
        if (cancelled || !containerRef.current) return;
        maplibre.setWorkerUrl(WORKER_URL);
        map = new maplibre.Map({
          container: containerRef.current,
          style: MAP_STYLE,
          center: [-74, 4.5],
          zoom: 4.2,
          attributionControl: { compact: true },
        });
        map.addControl(new maplibre.NavigationControl({ showCompass: false }), "top-right");
        map.on("load", () => {
          if (!map) return;
          map.addSource(SOURCE_ID, { type: "geojson", data: { type: "FeatureCollection", features: [] }, promoteId: "id" });
          map.addLayer({
            id: "proyectos-relleno",
            type: "fill",
            source: SOURCE_ID,
            paint: {
              "fill-color": ["get", "color"],
              "fill-opacity": ["case", ["boolean", ["feature-state", "highlight"], false], 0.9, 0.55],
            },
          });
          map.addLayer({
            id: "proyectos-borde",
            type: "line",
            source: SOURCE_ID,
            paint: {
              "line-color": "#f4f1e4",
              "line-width": ["case", ["boolean", ["feature-state", "highlight"], false], 3, 1.5],
            },
          });
          map.on("mousemove", "proyectos-relleno", (event) => {
            const id = Number(event.features?.[0]?.properties?.id);
            if (!Number.isFinite(id)) return;
            map!.getCanvas().style.cursor = "pointer";
            setHoverId(id);
            handlers.current.onHighlight(id);
          });
          map.on("mouseleave", "proyectos-relleno", () => {
            map!.getCanvas().style.cursor = "";
            setHoverId(null);
            handlers.current.onHighlight(null);
          });
          map.on("click", "proyectos-relleno", (event) => {
            const id = Number(event.features?.[0]?.properties?.id);
            if (Number.isFinite(id)) handlers.current.onSelect(id);
          });
          setReady(true);
        });
        map.on("error", (event) => {
          // Un mosaico que no carga no es grave; solo se avisa si el mapa en sí falla.
          if (event.error && !String(event.error.message).includes("Failed to fetch")) setFailed(true);
        });
        mapRef.current = map;
      })
      .catch(() => setFailed(true));

    return () => {
      cancelled = true;
      map?.remove();
      mapRef.current = null;
      highlighted.current = null;
      setReady(false);
    };
  }, []);

  // Actualiza los polígonos y encuadra el mapa cuando cambian los filtros.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    (map.getSource(SOURCE_ID) as GeoJSONSource | undefined)?.setData(collection);
    const bounds = boundsOf(items.map((item) => item.geometry));
    if (bounds) {
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      map.fitBounds(bounds, { padding: 48, maxZoom: 9, duration: reduceMotion ? 0 : 600 });
    }
  }, [collection, items, ready]);

  // Resalta el polígono que corresponde a la tarjeta (o al revés).
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const previous = highlighted.current;
    if (previous !== null && previous !== highlightId) {
      map.setFeatureState({ source: SOURCE_ID, id: previous }, { highlight: false });
    }
    if (highlightId !== null) map.setFeatureState({ source: SOURCE_ID, id: highlightId }, { highlight: true });
    highlighted.current = highlightId;
  }, [highlightId, ready]);

  const hovered = items.find((item) => item.id === hoverId);

  return (
    <div className="relative overflow-hidden rounded-3xl bg-forest">
      <div
        ref={containerRef}
        className="h-[420px] w-full md:h-[560px]"
        role="application"
        aria-label="Mapa interactivo de proyectos coloreados por categoría del índice. La lista junto al mapa ofrece las mismas opciones con teclado."
      />
      {failed && (
        <p role="alert" className="glass absolute inset-x-4 top-4 rounded-2xl px-4 py-3 text-sm text-forest-foreground">
          No pudimos cargar el mapa. Puedes elegir un proyecto en la lista.
        </p>
      )}
      {hovered && (
        <div className="glass pointer-events-none absolute top-4 left-4 rounded-2xl px-4 py-3 text-forest-foreground">
          <p className="text-sm font-semibold">{hovered.name}</p>
          <p className="text-xs text-forest-muted">
            {hovered.country ?? "País sin dato"} · {hovered.category ?? "Sin auditoría"}
          </p>
        </div>
      )}
      <ul className="glass absolute right-4 bottom-8 flex flex-wrap gap-3 rounded-2xl px-4 py-3 text-xs text-forest-foreground" aria-label="Leyenda">
        {CATEGORIES.map((category) => (
          <li key={category} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: categoryHex[category] }} aria-hidden />
            {category}
          </li>
        ))}
      </ul>
    </div>
  );
}
