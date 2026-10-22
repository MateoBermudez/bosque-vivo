import { Info } from "lucide-react";
import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";

import { PageHeader } from "@/components/common/page-header";
import { SampleBadge } from "@/components/common/sample-badge";
import { ErrorState, Loading } from "@/components/common/states";
import { Explorer, type ExplorerRow } from "@/components/projects/explorer";
import { attempt, isDemoProject, loadExplorerItems, showSampleNotice } from "@/lib/api";
import { isPartialResult, normalizeConfidence, readPermanence } from "@/lib/domain";

export const metadata: Metadata = {
  title: "Explorador de proyectos",
  description:
    "Mapa y lista de proyectos de carbono forestal con su índice de credibilidad y nivel de confianza.",
};

export default function ProjectsPage() {
  return (
    <>
      <PageHeader eyebrow="Explorador" title="Proyectos de carbono forestal">
        Elige un proyecto en el mapa o en la lista para ver lo declarado frente a lo observado.
      </PageHeader>
      <Suspense fallback={<Loading label="Cargando proyectos…" />}>
        <ExplorerLoader />
      </Suspense>
    </>
  );
}

async function ExplorerLoader() {
  await connection();
  const result = await attempt(loadExplorerItems);
  if (!result.ok) {
    return (
      <div className="mx-auto max-w-3xl px-5">
        <ErrorState message={result.message} />
      </div>
    );
  }
  const rows: ExplorerRow[] = result.data.map(({ project, geometry, audit }) => ({
    id: project.id,
    name: project.name,
    country: project.country,
    projectType: project.project_type,
    startYear: project.start_year,
    areaHa: project.area_ha,
    score: audit?.result?.score ?? null,
    category: audit?.result?.category ?? null,
    confidence: audit?.result ? normalizeConfidence(audit.result.confidence_label) : null,
    geometry: geometry?.geometry ?? null,
    partialPermanence: audit?.result && isPartialResult(audit.result) ? readPermanence(audit.result) : null,
    demo: isDemoProject(project),
  }));
  const allSample = showSampleNotice();
  const someDemo = rows.some((row) => row.demo);
  return (
    <>
      {allSample && (
        <div className="mx-auto mb-4 max-w-7xl px-5">
          <SampleBadge />
        </div>
      )}
      {!allSample && someDemo && (
        <p className="mx-auto mb-4 flex max-w-7xl items-start gap-2 px-5 text-sm text-muted-foreground">
          <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          Los proyectos marcados «Demostración» son ficticios: sirven para ver cómo se ve una auditoría completa.
          Los demás son proyectos reales cuya auditoría aún no se ha calculado.
        </p>
      )}
      <Explorer rows={rows} />
    </>
  );
}
