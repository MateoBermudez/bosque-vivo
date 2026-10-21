import { ArrowLeft, Download, MessageSquare } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";

import { EmptyState, ErrorState, Loading } from "@/components/common/states";
import { SampleBadge } from "@/components/common/sample-badge";
import { BeforeAfter } from "@/components/projects/before-after";
import { ComparisonTable } from "@/components/projects/comparison-table";
import { LossChart } from "@/components/projects/loss-chart";
import { NdviChart } from "@/components/projects/ndvi-chart";
import { ScoreCard } from "@/components/projects/score-card";
import { attempt, dataSource, loadProjectView, showSampleNotice } from "@/lib/api";
import { readSensorKey } from "@/lib/domain";
import { formatDateTime, formatHa, formatPercent } from "@/lib/format";

export const metadata: Metadata = {
  title: "Detalle de proyecto",
  description:
    "Índice de credibilidad, serie NDVI, pérdida de bosque y comparación entre lo declarado y lo observado.",
};

export default function ProjectPage({ params }: PageProps<"/proyectos/[id]">) {
  return (
    <div className="mx-auto max-w-7xl px-5 pt-8">
      <Link
        href="/proyectos"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden /> Volver al explorador
      </Link>
      <Suspense fallback={<Loading label="Cargando proyecto…" />}>
        <ProjectDetail params={params} />
      </Suspense>
    </div>
  );
}

async function ProjectDetail({ params }: Pick<PageProps<"/proyectos/[id]">, "params">) {
  await connection();
  const { id: rawId } = await params;
  const id = Number(rawId);
  if (!Number.isInteger(id) || id < 1) notFound();

  const result = await attempt(() => loadProjectView(id));
  if (!result.ok) return <ErrorState message={result.message} />;
  if (!result.data) notFound();

  const { project, series, audit } = result.data;
  const auditResult = audit?.result ?? null;
  const sensorKey = auditResult ? readSensorKey(auditResult) : null;
  const usedPoints = series?.ndvi.filter((point) => sensorKey === null || point.sensor === sensorKey) ?? [];
  const averageValid = usedPoints.length
    ? usedPoints.reduce((sum, point) => sum + point.valid_fraction, 0) / usedPoints.length
    : null;
  const scenes = usedPoints.reduce((sum, point) => sum + point.scene_count, 0);
  const isMock = dataSource() === "mock";

  return (
    <>
      <header className="mt-4 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div>
          {showSampleNotice() && <SampleBadge />}
          <h1 className="mt-4 text-4xl font-extrabold md:text-5xl">{project.name}</h1>
          <dl className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
            <div>
              <dt className="sr-only">Registro</dt>
              <dd>
                {project.source_registry} · {project.registry_id}
              </dd>
            </div>
            <div>
              <dt className="sr-only">País</dt>
              <dd>{project.country ?? "País sin dato"}</dd>
            </div>
            {project.project_type && (
              <div>
                <dt className="sr-only">Tipo</dt>
                <dd>{project.project_type}</dd>
              </div>
            )}
            {project.start_year && (
              <div>
                <dt className="sr-only">Inicio</dt>
                <dd>Inicio {project.start_year}</dd>
              </div>
            )}
            <div>
              <dt className="sr-only">Área</dt>
              <dd>{formatHa(project.area_ha)}</dd>
            </div>
          </dl>
          {auditResult?.narrative && <p className="mt-6 max-w-2xl text-lg">{auditResult.narrative}</p>}
          <div className="mt-6 flex flex-wrap gap-3">
            {audit && (
              <a href={`/informe/${audit.id}`} className="btn-dark">
                <Download className="h-4 w-4" aria-hidden /> Descargar reporte
              </a>
            )}
            <Link href={`/chat?proyecto=${project.id}`} className="btn-outline">
              <MessageSquare className="h-4 w-4" aria-hidden /> Preguntar al asistente sobre este proyecto
            </Link>
          </div>
        </div>
        {auditResult ? (
          <ScoreCard result={auditResult} />
        ) : (
          <EmptyState title="Este proyecto aún no tiene auditoría">
            Cuando se calcule el índice, aquí aparecerán el puntaje, la confianza y el detalle por componente.
          </EmptyState>
        )}
      </header>

      <section className="mt-10 grid gap-6 lg:grid-cols-2" aria-label="Series de tiempo">
        <div className="card-soft p-6">
          <h2 className="text-xl font-bold">Verdor (NDVI) en el tiempo</h2>
          <p className="text-sm text-muted-foreground">La línea punteada marca el inicio de la acreditación (T0).</p>
          <div className="mt-4">
            <NdviChart points={series?.ndvi ?? []} t0={series?.t0 ?? null} />
          </div>
        </div>
        <div className="card-soft p-6">
          <h2 className="text-xl font-bold">Pérdida de bosque por año</h2>
          <p className="text-sm text-muted-foreground">Hectáreas, según Hansen Global Forest Change.</p>
          <div className="mt-4">
            <LossChart loss={series?.loss ?? []} />
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_1fr]" aria-label="Imágenes y comparación">
        {isMock ? (
          <BeforeAfter
            before="/images/sat-before.jpg"
            after="/images/sat-after.jpg"
            beforeLabel="Antes (T0)"
            afterLabel="Después (reciente)"
            simulated
          />
        ) : (
          <EmptyState title="Imágenes antes y después">
            Todavía no están disponibles desde el servidor. Aparecerán aquí cuando se generen las miniaturas del
            proyecto.
          </EmptyState>
        )}
        <ComparisonTable rows={series?.comparison ?? []} />
      </section>

      <section className="mt-6 grid gap-6 md:grid-cols-2" aria-label="Calidad y reproducibilidad">
        <div className="card-soft p-6">
          <h2 className="text-xl font-bold">Calidad de los datos</h2>
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="rounded-2xl bg-secondary p-4">
              <p className="text-3xl font-extrabold">{averageValid === null ? "—" : formatPercent(averageValid)}</p>
              <p className="text-sm text-muted-foreground">píxeles válidos (promedio)</p>
            </div>
            <div className="rounded-2xl bg-secondary p-4">
              <p className="text-3xl font-extrabold">{scenes.toLocaleString("es-CO")}</p>
              <p className="text-sm text-muted-foreground">escenas analizadas</p>
            </div>
          </div>
        </div>
        <div className="card-soft p-6">
          <h2 className="text-xl font-bold">Reproducibilidad</h2>
          {audit ? (
            <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
              <dt className="text-muted-foreground">Corrida</dt>
              <dd className="font-mono">#{audit.id}</dd>
              <dt className="text-muted-foreground">Versión del índice</dt>
              <dd className="font-mono">{audit.index_version}</dd>
              <dt className="text-muted-foreground">Código (git sha)</dt>
              <dd className="font-mono">{audit.git_sha ?? "—"}</dd>
              {Object.entries(audit.dataset_versions).map(([name, value]) => (
                <div key={name} className="contents">
                  <dt className="text-muted-foreground">{name}</dt>
                  <dd className="font-mono break-all">{String(value)}</dd>
                </div>
              ))}
              <dt className="text-muted-foreground">Fecha del cálculo</dt>
              <dd className="font-mono">{formatDateTime(audit.created_at)}</dd>
            </dl>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">Se mostrará cuando exista una auditoría.</p>
          )}
        </div>
      </section>
    </>
  );
}
