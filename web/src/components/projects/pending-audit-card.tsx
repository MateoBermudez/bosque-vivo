import { Check, Clock, Info } from "lucide-react";

import type { ProjectKind } from "@/lib/profile";
import { cn } from "@/lib/utils";

interface Step {
  label: string;
  detail: string;
  done: boolean;
}

export function PendingAuditCard({
  kind,
  hasPolygon,
  creditingStart,
}: {
  kind: ProjectKind | null;
  hasPolygon: boolean;
  creditingStart: string | null;
}) {
  const steps: Step[] = [
    { label: "Contorno del proyecto", detail: "Polígono público cargado", done: hasPolygon },
    { label: "Fecha de inicio (T0)", detail: creditingStart ? "Tomada del registro" : "Sin dato", done: Boolean(creditingStart) },
    { label: "Pérdida de bosque por año", detail: "Mapa de Hansen (Earth Engine)", done: false },
    { label: "Verdor (NDVI) en el tiempo", detail: "Sentinel-2 y Landsat", done: false },
    { label: "Índice de credibilidad", detail: "Se calcula con lo anterior", done: false },
  ];

  return (
    <section aria-labelledby="titulo-pendiente" className="rounded-[2rem] bg-forest p-6 text-forest-foreground">
      <h2 id="titulo-pendiente" className="text-sm font-normal text-forest-muted">
        Estado de la auditoría
      </h2>
      <p className="mt-2 text-2xl font-extrabold">Pendiente de cálculo</p>
      <p className="mt-2 text-sm text-forest-muted">
        Este proyecto ya está cargado con su contorno real. Falta calcular las series satelitales; cuando
        estén, aquí aparecerán el índice y su confianza.
      </p>
      <ol className="mt-5 space-y-3">
        {steps.map((step) => (
          <li key={step.label} className="flex items-start gap-3">
            <span
              className={cn(
                "mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full",
                step.done ? "bg-lime text-lime-foreground" : "bg-forest-foreground/10 text-forest-muted",
              )}
            >
              {step.done ? <Check className="h-3.5 w-3.5" aria-hidden /> : <Clock className="h-3.5 w-3.5" aria-hidden />}
              <span className="sr-only">{step.done ? "Listo" : "Pendiente"}</span>
            </span>
            <div>
              <p className="text-sm font-semibold">{step.label}</p>
              <p className="text-xs text-forest-muted">{step.detail}</p>
            </div>
          </li>
        ))}
      </ol>
      {kind === "ARR" && (
        <p className="glass mt-5 flex items-start gap-2 rounded-2xl p-4 text-xs">
          <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          Es un proyecto de reforestación. El índice actual mide la permanencia de bosque que ya existía, así que
          todavía no lo cubre y el resultado esperado es «Insuficiente». No indica un problema del proyecto.
        </p>
      )}
    </section>
  );
}
