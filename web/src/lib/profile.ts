import type { Declaration } from "./api/schema";

export type ProjectKind = "AD" | "ARR" | "IFM";

export interface ProjectProfile {
  creditingStart: string | null;
  creditingEnd: string | null;
  methodology: string | null;
  developer: string | null;
  processingApproach: string | null;
  geometrySource: string | null;
  sourceDocument: string | null;
}

/** Reúne las declaraciones del proyecto en un objeto con nombres propios. */
export function buildProfile(declarations: Declaration[]): ProjectProfile {
  const value = (field: string) => declarations.find((d) => d.field === field)?.value ?? null;
  return {
    creditingStart: value("crediting_start"),
    creditingEnd: value("crediting_end"),
    methodology: value("methodology"),
    developer: value("developer"),
    processingApproach: value("processing_approach"),
    geometrySource: value("geometry_source"),
    sourceDocument: declarations.find((d) => d.source_document)?.source_document ?? null,
  };
}

/** «Deforestación evitada (AD)» → «AD». */
export function projectKind(projectType: string | null): ProjectKind | null {
  const match = projectType?.match(/\((AD|ARR|IFM)\)\s*$/);
  return (match?.[1] as ProjectKind | undefined) ?? null;
}

export const KIND_NOTES: Record<ProjectKind, string> = {
  AD: "Busca evitar la deforestación que ocurriría sin el proyecto.",
  ARR: "Planta o restaura bosque en tierras degradadas.",
  IFM: "Mejora el manejo de bosques que ya existen.",
};

export const APPROACH_NOTES: Record<string, string> = {
  Official: "Contorno oficial, tomado del registro o entregado por el desarrollador.",
  Georeferenced:
    "Contorno digitalizado a mano desde los mapas del documento del proyecto: puede diferir del real.",
  Method: "Contorno reconstruido siguiendo el protocolo descrito en el documento del proyecto.",
  Linear: "Contorno construido a partir de líneas publicadas por el registro.",
};

/** Solo Verra tiene un patrón de URL estable; para los demás registros no se inventa un enlace. */
export function registryUrl(registry: string, registryId: string): string | null {
  const verra = registryId.match(/^VCS-?0*(\d+)$/i);
  if (registry.toLowerCase() === "verra" && verra) {
    return `https://registry.verra.org/app/projectDetail/VCS/${verra[1]}`;
  }
  return null;
}

/** «2013-11-14» → «14 nov 2013» (las fechas del registro no llevan hora). */
export function formatDateOnly(iso: string): string {
  const date = new Date(`${iso.slice(0, 10)}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" })
    .format(date)
    .replace(/\./g, "");
}
