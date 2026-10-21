"use client";

import Image from "next/image";
import { useId, useState } from "react";

import { cn } from "@/lib/utils";

type Mode = "natural" | "falso" | "ndvi";

const MODES: { id: Mode; label: string }[] = [
  { id: "natural", label: "Color natural" },
  { id: "falso", label: "Falso color" },
  { id: "ndvi", label: "NDVI" },
];

// Aproximación visual para la maqueta: con la API real cada modo será una imagen distinta.
const FILTERS: Record<Mode, string> = {
  natural: "none",
  falso: "hue-rotate(260deg) saturate(1.6)",
  ndvi: "grayscale(1) contrast(1.6) sepia(1) hue-rotate(50deg) saturate(3)",
};

export function BeforeAfter({
  before,
  after,
  beforeLabel,
  afterLabel,
  simulated,
}: {
  before: string;
  after: string;
  beforeLabel: string;
  afterLabel: string;
  /** `true` cuando las imágenes son de ejemplo y los modos se simulan con filtros. */
  simulated: boolean;
}) {
  const sliderId = useId();
  const [position, setPosition] = useState(50);
  const [mode, setMode] = useState<Mode>("natural");
  const filter = simulated ? FILTERS[mode] : "none";

  return (
    <div className="card-soft p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-bold">Antes y después</h2>
        {simulated && (
          <div className="flex rounded-full bg-secondary p-1 text-xs font-semibold" role="group" aria-label="Tipo de imagen">
            {MODES.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setMode(item.id)}
                aria-pressed={mode === item.id}
                className={cn(
                  "rounded-full px-3 py-1.5",
                  mode === item.id ? "bg-forest text-forest-foreground" : "text-muted-foreground",
                )}
              >
                {item.label}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="relative mt-4 aspect-[4/3] overflow-hidden rounded-2xl">
        <Image
          src={after}
          alt={`Imagen satelital: ${afterLabel}`}
          fill
          sizes="(min-width: 1024px) 40vw, 100vw"
          className="object-cover"
          style={{ filter }}
        />
        <Image
          src={before}
          alt={`Imagen satelital: ${beforeLabel}`}
          fill
          sizes="(min-width: 1024px) 40vw, 100vw"
          className="object-cover"
          style={{ filter, clipPath: `inset(0 ${100 - position}% 0 0)` }}
        />
        <div className="absolute inset-y-0 w-0.5 bg-forest-foreground" style={{ left: `${position}%` }} aria-hidden />
        <span className="glass absolute top-3 left-3 rounded-full px-3 py-1 text-xs text-forest-foreground">{beforeLabel}</span>
        <span className="glass absolute top-3 right-3 rounded-full px-3 py-1 text-xs text-forest-foreground">{afterLabel}</span>
      </div>
      <label htmlFor={sliderId} className="sr-only">
        Deslizar entre antes y después
      </label>
      <input
        id={sliderId}
        type="range"
        min={0}
        max={100}
        value={position}
        onChange={(event) => setPosition(Number(event.target.value))}
        className="mt-4 w-full accent-[var(--primary)]"
      />
    </div>
  );
}
