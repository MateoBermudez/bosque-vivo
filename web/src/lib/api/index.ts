import "server-only";

import { BackendError, liveApi } from "./backend";
import { mockApi } from "./mock";
import type { AuditRun, Category, Declaration, Project, ProjectGeometry, Series } from "./schema";
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

/**
 * Para el mapa de país basta un contorno aproximado: 0,005° ≈ 550 m y las 200 partes más grandes
 * (hay proyectos formados por miles de parcelas diminutas que no se distinguen a esa escala).
 */
const MAP_SIMPLIFY_DEGREES = 0.005;
const MAP_MAX_PARTS = 200;
const EXPLORER_BATCH = 8;

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
  // Por tandas: pedir todo a la vez (cientos de peticiones) satura la API y vence los tiempos de espera.
  const items: ExplorerItem[] = [];
  for (let from = 0; from < projects.length; from += EXPLORER_BATCH) {
    const batch = projects.slice(from, from + EXPLORER_BATCH);
    items.push(
      ...(await Promise.all(
        batch.map(async (project) => {
          const [geometry, audit] = await Promise.all([
            api.getGeometry(project.id, { simplify: MAP_SIMPLIFY_DEGREES, maxParts: MAP_MAX_PARTS }),
            api.getLatestAudit(project.id),
          ]);
          return { project, geometry, audit, category: audit?.result?.category ?? null };
        }),
      )),
    );
  }
  return items;
}

export interface ProjectView {
  project: Project;
  series: Series | null;
  audit: AuditRun | null;
  declarations: Declaration[];
  /** Polígono aligerado para el mapa del proyecto (~55 m de tolerancia). */
  geometry: ProjectGeometry | null;
}

export async function loadProjectView(id: number): Promise<ProjectView | null> {
  const api = getApi();
  const project = await api.getProject(id);
  if (!project) return null;
  const [series, audit, declarations, geometry] = await Promise.all([
    api.getSeries(id),
    api.getLatestAudit(id),
    api.getDeclarations(id),
    api.getGeometry(id, { simplify: 0.0005, maxParts: 1000 }),
  ]);
  return { project, series, audit, declarations, geometry };
}
