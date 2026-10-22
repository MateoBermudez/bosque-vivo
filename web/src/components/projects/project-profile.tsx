import { ExternalLink } from "lucide-react";

import type { Project } from "@/lib/api/schema";
import { formatHa } from "@/lib/format";
import {
  APPROACH_NOTES,
  KIND_NOTES,
  formatDateOnly,
  projectKind,
  registryUrl,
  type ProjectProfile as Profile,
} from "@/lib/profile";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1 border-t border-border py-3 first:border-t-0 sm:grid-cols-[11rem_1fr] sm:gap-4">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium">{children}</dd>
    </div>
  );
}

export function ProjectProfileCard({ project, profile }: { project: Project; profile: Profile }) {
  const kind = projectKind(project.project_type);
  const link = registryUrl(project.source_registry, project.registry_id);
  const approachNote = profile.processingApproach ? APPROACH_NOTES[profile.processingApproach] : null;
  const period =
    profile.creditingStart &&
    `${formatDateOnly(profile.creditingStart)}${profile.creditingEnd ? ` – ${formatDateOnly(profile.creditingEnd)}` : ""}`;

  return (
    <section className="card-soft p-6" aria-labelledby="titulo-ficha">
      <h2 id="titulo-ficha" className="text-xl font-bold">
        Ficha del proyecto
      </h2>
      <dl className="mt-3">
        <Row label="Registro">
          {project.source_registry} · {project.registry_id}
          {link && (
            <a
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 inline-flex items-center gap-1 text-primary underline underline-offset-4"
            >
              Ver en el registro <ExternalLink className="h-3 w-3" aria-hidden />
            </a>
          )}
        </Row>
        {project.project_type && (
          <Row label="Tipo">
            {project.project_type}
            {kind && <span className="mt-0.5 block font-normal text-muted-foreground">{KIND_NOTES[kind]}</span>}
          </Row>
        )}
        <Row label="País">{project.country ?? "Sin dato"}</Row>
        {profile.developer && <Row label="Desarrollador">{profile.developer}</Row>}
        {profile.methodology && <Row label="Metodología">{profile.methodology}</Row>}
        {period && (
          <Row label="Periodo de acreditación">
            {period}
            <span className="mt-0.5 block font-normal text-muted-foreground">
              Su inicio es el T0: separa el «antes» y el «después» al medir.
            </span>
          </Row>
        )}
        <Row label="Área">{formatHa(project.area_ha)}</Row>
        {profile.geometrySource && (
          <Row label="Contorno analizado">
            {profile.geometrySource}
            {approachNote && <span className="mt-0.5 block font-normal text-muted-foreground">{approachNote}</span>}
          </Row>
        )}
        {profile.sourceDocument && <Row label="Fuente de los datos">{profile.sourceDocument}</Row>}
      </dl>
    </section>
  );
}
