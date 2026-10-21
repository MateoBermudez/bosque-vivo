"use client";

import { ChevronRight, Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useId, useMemo, useState } from "react";

import { CategoryPill } from "@/components/common/category-pill";
import { EmptyState } from "@/components/common/states";
import type { Category, ProjectGeometry } from "@/lib/api/schema";
import { CATEGORIES } from "@/lib/api/schema";
import type { ConfidenceLabel } from "@/lib/domain";
import { formatHa } from "@/lib/format";

import { ProjectMap, type MapItem } from "./project-map";

export interface ExplorerRow {
  id: number;
  name: string;
  country: string | null;
  projectType: string | null;
  startYear: number | null;
  areaHa: number | null;
  score: number | null;
  category: Category | null;
  confidence: ConfidenceLabel | null;
  geometry: ProjectGeometry["geometry"] | null;
}

const field =
  "h-11 w-full rounded-full border border-input bg-background px-4 text-sm placeholder:text-muted-foreground";

export function Explorer({ rows }: { rows: ExplorerRow[] }) {
  const router = useRouter();
  const ids = useId();
  const [term, setTerm] = useState("");
  const [country, setCountry] = useState("");
  const [category, setCategory] = useState<Category | "">("");
  const [min, setMin] = useState(0);
  const [highlightId, setHighlightId] = useState<number | null>(null);

  const countries = useMemo(
    () => [...new Set(rows.map((row) => row.country).filter((value): value is string => Boolean(value)))].sort(),
    [rows],
  );

  const visible = useMemo(() => {
    const needle = term.trim().toLowerCase();
    return rows.filter(
      (row) =>
        (!country || row.country === country) &&
        (!category || row.category === category) &&
        (min === 0 || (row.score !== null && row.score >= min)) &&
        row.name.toLowerCase().includes(needle),
    );
  }, [rows, term, country, category, min]);

  const mapItems = useMemo<MapItem[]>(
    () =>
      visible.flatMap((row) =>
        row.geometry
          ? [{ id: row.id, name: row.name, country: row.country, category: row.category, geometry: row.geometry }]
          : [],
      ),
    [visible],
  );

  const select = useCallback((id: number) => router.push(`/proyectos/${id}`), [router]);

  return (
    <div className="mx-auto max-w-7xl px-5">
      <form
        className="card-soft grid gap-3 p-4 md:grid-cols-4"
        role="search"
        aria-label="Filtrar proyectos"
        onSubmit={(event) => event.preventDefault()}
      >
        <div className="relative">
          <label htmlFor={`${ids}-buscar`} className="sr-only">
            Buscar por nombre
          </label>
          <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <input
            id={`${ids}-buscar`}
            type="search"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            placeholder="Buscar por nombre"
            className={`${field} pl-9`}
          />
        </div>
        <div>
          <label htmlFor={`${ids}-pais`} className="sr-only">
            País
          </label>
          <select id={`${ids}-pais`} value={country} onChange={(event) => setCountry(event.target.value)} className={field}>
            <option value="">Todos los países</option>
            {countries.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor={`${ids}-categoria`} className="sr-only">
            Categoría
          </label>
          <select
            id={`${ids}-categoria`}
            value={category}
            onChange={(event) => setCategory(event.target.value as Category | "")}
            className={field}
          >
            <option value="">Todas las categorías</option>
            {CATEGORIES.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-3 px-2 text-sm">
          <label htmlFor={`${ids}-min`} className="whitespace-nowrap text-muted-foreground">
            Índice ≥ {min}
          </label>
          <input
            id={`${ids}-min`}
            type="range"
            min={0}
            max={100}
            step={5}
            value={min}
            onChange={(event) => setMin(Number(event.target.value))}
            className="w-full accent-[var(--primary)]"
          />
        </div>
      </form>

      <p className="mt-4 text-sm text-muted-foreground" role="status">
        {visible.length} de {rows.length} proyectos
      </p>

      <div className="mt-2 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <ProjectMap items={mapItems} highlightId={highlightId} onHighlight={setHighlightId} onSelect={select} />
        <ul className="space-y-3">
          {visible.length === 0 && (
            <li>
              <EmptyState title="Sin resultados">Ningún proyecto coincide con los filtros. Prueba ampliarlos.</EmptyState>
            </li>
          )}
          {visible.map((row) => (
            <li key={row.id}>
              <Link
                href={`/proyectos/${row.id}`}
                className="card-soft flex items-center gap-4 p-4 transition hover:-translate-y-0.5 data-[active=true]:ring-2 data-[active=true]:ring-ring"
                data-active={highlightId === row.id}
                onMouseEnter={() => setHighlightId(row.id)}
                onMouseLeave={() => setHighlightId(null)}
                onFocus={() => setHighlightId(row.id)}
                onBlur={() => setHighlightId(null)}
              >
                <div className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-forest text-xl font-extrabold text-lime">
                  {row.score === null ? "–" : Math.round(row.score)}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-bold">{row.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {[
                      row.country ?? "País sin dato",
                      row.projectType,
                      row.startYear ? `desde ${row.startYear}` : null,
                      row.areaHa ? formatHa(row.areaHa) : null,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {row.category ? (
                      <CategoryPill category={row.category} />
                    ) : (
                      <span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-semibold">Sin auditoría</span>
                    )}
                    {row.confidence && (
                      <span className="rounded-full border border-border px-2.5 py-1 text-xs">
                        Confianza {row.confidence.toLowerCase()}
                      </span>
                    )}
                  </div>
                </div>
                <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground" aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
