"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import type { Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";

import type { Category, ProjectGeometry } from "@/lib/api/schema";
import { categoryHex } from "@/lib/domain";

import { MAP_STYLE, WORKER_URL, boundsOf } from "./map-style";

/** Mapa satelital con el polígono de un proyecto, encuadrado sobre él. */
export function LocationMap({
  geometry,
  category,
  name,
}: {
  geometry: ProjectGeometry;
  category: Category | null;
  name: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let map: MapLibreMap | null = null;

    import("maplibre-gl")
      .then((maplibre) => {
        if (cancelled || !containerRef.current) return;
        maplibre.setWorkerUrl(WORKER_URL);
        const bounds = boundsOf([geometry.geometry]);
        map = new maplibre.Map({
          container: containerRef.current,
          style: MAP_STYLE,
          bounds: bounds ?? undefined,
          fitBoundsOptions: { padding: 40, maxZoom: 13 },
          center: bounds ? undefined : [-74, 4.5],
          zoom: bounds ? undefined : 5,
          attributionControl: { compact: true },
        });
        map.addControl(new maplibre.NavigationControl({ showCompass: false }), "top-right");
        map.on("load", () => {
          if (!map) return;
          map.addSource("proyecto", { type: "geojson", data: geometry as GeoJSON.Feature });
          map.addLayer({
            id: "proyecto-relleno",
            type: "fill",
            source: "proyecto",
            paint: {
              "fill-color": categoryHex[category ?? "Insuficiente"],
              "fill-opacity": 0.4,
            },
          });
          map.addLayer({
            id: "proyecto-borde",
            type: "line",
            source: "proyecto",
            paint: { "line-color": "#f4f1e4", "line-width": 2 },
          });
        });
        map.on("error", (event) => {
          if (event.error && !String(event.error.message).includes("Failed to fetch")) setFailed(true);
        });
      })
      .catch(() => setFailed(true));

    return () => {
      cancelled = true;
      map?.remove();
    };
  }, [geometry, category]);

  return (
    <div className="relative overflow-hidden rounded-3xl bg-forest">
      <div
        ref={containerRef}
        className="h-[340px] w-full md:h-[420px]"
        role="application"
        aria-label={`Mapa satelital con el contorno de ${name}.`}
      />
      {failed && (
        <p role="alert" className="glass absolute inset-x-4 top-4 rounded-2xl px-4 py-3 text-sm text-forest-foreground">
          No pudimos cargar el mapa.
        </p>
      )}
    </div>
  );
}
