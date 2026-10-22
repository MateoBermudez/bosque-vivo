import { CheckCircle2, CircleSlash, XCircle } from "lucide-react";
import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";

import { PageHeader } from "@/components/common/page-header";
import { SampleBadge } from "@/components/common/sample-badge";
import { EmptyState, ErrorState, Loading } from "@/components/common/states";
import { attempt, getApi, showSampleNotice } from "@/lib/api";
import type { Trace } from "@/lib/api/schema";
import { queryClassLabel, roleLabel, toolLabel } from "@/lib/domain";
import { formatLatency } from "@/lib/format";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Trazas del agente",
  description: "Registro de las consultas al agente: herramientas usadas, validación de cifras y latencia.",
  robots: { index: false },
};

export default function TracesPage() {
  return (
    <>
      <PageHeader eyebrow="Auditor" title="Trazas del agente">
        Cada consulta queda registrada con las herramientas que usó, el modelo, la versión del prompt y si pasó la
        validación de cifras. Contiene preguntas de usuarios: no la compartas.
      </PageHeader>
      <div className="mx-auto max-w-7xl px-5">
        <Suspense fallback={<Loading label="Cargando trazas…" />}>
          <TraceList />
        </Suspense>
      </div>
    </>
  );
}

async function TraceList() {
  await connection();
  const result = await attempt(() => getApi().traces(50));
  if (!result.ok) return <ErrorState message={result.message} />;
  if (result.data.length === 0) {
    return <EmptyState title="Todavía no hay consultas">Cuando el agente responda, aparecerán aquí.</EmptyState>;
  }
  return (
    <>
      {showSampleNotice() && (
        <div className="mb-4">
          <SampleBadge />
        </div>
      )}
      <ul className="space-y-3">
        {result.data.map((trace) => (
          <li key={trace.id}>
            <TraceItem trace={trace} />
          </li>
        ))}
      </ul>
    </>
  );
}

function Validation({ trace }: { trace: Trace }) {
  if (trace.validator_passed === true) {
    return (
      <span className="inline-flex items-center gap-1 text-cat-alta">
        <CheckCircle2 className="h-4 w-4" aria-hidden /> Aprobada
      </span>
    );
  }
  if (trace.validator_passed === false) {
    return (
      <span className="inline-flex items-center gap-1 text-cat-baja">
        <XCircle className="h-4 w-4" aria-hidden /> Rechazada
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-muted-foreground">
      <CircleSlash className="h-4 w-4" aria-hidden /> Sin validar
    </span>
  );
}

function TraceItem({ trace }: { trace: Trace }) {
  return (
    <details id={`traza-${trace.id}`} className="card-soft group p-5 target:ring-2 target:ring-ring">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-x-4 gap-y-2">
        <span className="font-mono text-sm text-muted-foreground">#{trace.id}</span>
        <span className="min-w-0 flex-1 basis-60 truncate font-semibold">{trace.query}</span>
        <span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-semibold">{roleLabel(trace.role)}</span>
        <span
          className={cn(
            "rounded-full px-2.5 py-1 text-xs font-semibold",
            trace.query_class === "profunda" ? "bg-forest text-forest-foreground" : "bg-secondary",
          )}
        >
          {queryClassLabel(trace.query_class)}
        </span>
        <span className="text-sm">
          <Validation trace={trace} />
        </span>
        <span className="text-sm tabular-nums text-muted-foreground">{formatLatency(trace.latency_ms)}</span>
      </summary>

      <div className="mt-4 grid gap-4 border-t border-border pt-4 text-sm md:grid-cols-2">
        <div>
          <h3 className="font-semibold">Pregunta</h3>
          <p className="mt-1 whitespace-pre-wrap text-muted-foreground">{trace.query}</p>
          <h3 className="mt-4 font-semibold">Respuesta</h3>
          <p className="mt-1 whitespace-pre-wrap text-muted-foreground">{trace.answer ?? "Sin respuesta registrada."}</p>
        </div>
        <div>
          <h3 className="font-semibold">Herramientas usadas</h3>
          {trace.tools.length === 0 ? (
            <p className="mt-1 text-muted-foreground">No usó herramientas.</p>
          ) : (
            <ol className="mt-1 list-decimal space-y-1 pl-5 text-muted-foreground">
              {trace.tools.map((tool, index) => (
                <li key={`${tool}-${index}`}>
                  {toolLabel(tool)} <span className="font-mono text-xs">({tool})</span>
                </li>
              ))}
            </ol>
          )}
          <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
            <dt className="text-muted-foreground">Modelo</dt>
            <dd className="font-mono">{trace.model ?? "—"}</dd>
            <dt className="text-muted-foreground">Versión del prompt</dt>
            <dd className="font-mono">{trace.prompt_version}</dd>
            <dt className="text-muted-foreground">Respaldo con plantilla</dt>
            <dd>{trace.used_fallback ? "Sí" : "No"}</dd>
          </dl>
        </div>
      </div>
    </details>
  );
}
