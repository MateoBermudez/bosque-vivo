import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";

import { PageHeader } from "@/components/common/page-header";
import { SampleBadge } from "@/components/common/sample-badge";
import { ErrorState, Loading } from "@/components/common/states";
import { Explorer, type ExplorerRow } from "@/components/projects/explorer";
import { attempt, isDemoProject, loadExplorerItems, showSampleNotice } from "@/lib/api";
import { normalizeConfidence } from "@/lib/domain";

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
  }));
  const sample = showSampleNotice() || result.data.some(({ project }) => isDemoProject(project));
  return (
    <>
      {sample && (
        <div className="mx-auto mb-4 max-w-7xl px-5">
          <SampleBadge />
        </div>
      )}
      <Explorer rows={rows} />
    </>
  );
}
