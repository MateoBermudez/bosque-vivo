import Link from "next/link";

import { CategoryPill } from "@/components/common/category-pill";
import { categorySchema, type CommunityProject } from "@/lib/api/schema";

const number = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1 });

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-semibold">{value}</dd>
    </div>
  );
}

export function ProjectCard({ project }: { project: CommunityProject }) {
  const category = categorySchema.safeParse(project.category);
  const place = [project.country, project.area_ha ? `${number.format(project.area_ha)} ha` : null].filter(Boolean);
  const hasScore = project.score !== null && project.score !== undefined;
  return (
    <article
      aria-label={`Ficha de ${project.name}`}
      className="w-full max-w-[85%] rounded-2xl border border-border bg-background p-4 text-sm"
    >
      <h3 className="font-bold">{project.name}</h3>
      {place.length > 0 && <p className="text-xs text-muted-foreground">{place.join(" · ")}</p>}
      <div className="mt-3 flex flex-wrap items-center gap-3">
        {category.success && <CategoryPill category={category.data} />}
        {hasScore ? (
          <span>
            <strong className="text-2xl">{number.format(project.score!)}</strong>{" "}
            <span className="text-muted-foreground">de 100</span>
          </span>
        ) : (
          <span className="text-muted-foreground">Todavía sin índice completo</span>
        )}
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
        {project.confidence_label && <Fact label="Confianza" value={project.confidence_label} />}
        {project.forest_standing_pct !== null && project.forest_standing_pct !== undefined && (
          <Fact label="Bosque en pie" value={`${number.format(project.forest_standing_pct)} %`} />
        )}
      </dl>
      <Link
        href={`/proyectos/${project.project_id}`}
        className="mt-3 inline-block text-xs font-semibold underline underline-offset-4"
      >
        Ver ficha completa
      </Link>
    </article>
  );
}
