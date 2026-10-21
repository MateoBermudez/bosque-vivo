import "server-only";

import { BackendError, liveApi } from "./backend";
import { mockApi } from "./mock";
import type { AuditRun, Category, Project, ProjectGeometry, Series } from "./schema";
import type { BosqueVivoApi } from "./types";

export { BackendError };
export type DataSource = "mock" | "live";

/**
 * `BV_DATA_SOURCE=live` usa la API real (BACKEND_URL). Cualquier otro valor usa datos de ejemplo.
 * El modo de ejemplo siempre muestra el aviso de "datos ilustrativos".
 */
export function dataSource(): DataSource {
  return process.env.BV_DATA_SOURCE === "live" ? "live" : "mock";
}

export function getApi(): BosqueVivoApi {
  return dataSource() === "live" ? liveApi : mockApi;
}

/** El aviso se muestra con datos de ejemplo, o en vivo si la base es la de demostración. */
export function showSampleNotice(): boolean {
  return dataSource() === "mock" || process.env.BV_SAMPLE_NOTICE === "1";
}

export type Attempt<T> = { ok: true; data: T } | { ok: false; message: string };

/** Convierte un fallo del backend en un mensaje para mostrar, en vez de romper la página. */
export async function attempt<T>(task: () => Promise<T>): Promise<Attempt<T>> {
  try {
    return { ok: true, data: await task() };
  } catch (error) {
    if (error instanceof BackendError) return { ok: false, message: error.message };
    console.error("[bosque-vivo] error inesperado", error);
    return { ok: false, message: "Ocurrió un error inesperado. Intenta de nuevo." };
  }
}

/** 0,002° ≈ 220 m: de sobra para un mapa de país y mucho más liviano que el polígono completo. */
const MAP_SIMPLIFY_DEGREES = 0.002;

/** Los proyectos de la base de demostración llevan el registro «demo». */
export function isDemoProject(project: Project): boolean {
  return project.source_registry.toLowerCase() === "demo";
}

export interface ExplorerItem {
  project: Project;
  geometry: ProjectGeometry | null;
  audit: AuditRun | null;
  category: Category | null;
}

/** Carga el listado con su geometría y su última auditoría (una consulta por proyecto). */
export async function loadExplorerItems(): Promise<ExplorerItem[]> {
  const api = getApi();
  const projects = await api.listProjects();
  return Promise.all(
    projects.map(async (project) => {
      const [geometry, audit] = await Promise.all([api.getGeometry(project.id, { simplify: MAP_SIMPLIFY_DEGREES }),
        api.getLatestAudit(project.id),]);
      return { project, geometry, audit, category: audit?.result?.category ?? null };
    }),
  );
}

export interface ProjectView {
  project: Project;
  series: Series | null;
  audit: AuditRun | null;
}

export async function loadProjectView(id: number): Promise<ProjectView | null> {
  const api = getApi();
  const project = await api.getProject(id);
  if (!project) return null;
  const [series, audit] = await Promise.all([api.getSeries(id), api.getLatestAudit(id)]);
  return { project, series, audit };
}
