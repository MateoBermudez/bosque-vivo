import "server-only";

import { readFile } from "node:fs/promises";
import path from "node:path";

import type { ZodType } from "zod";

import { BackendError } from "./backend";
import { auditRunSchema, declarationSchema, geometrySchema, projectSchema, seriesSchema } from "./schema";
import type { BosqueVivoApi, ReportFile } from "./types";

/** Copia de solo lectura generada con `scripts/export-snapshot.mjs`. */
const ROOT = path.join(process.cwd(), "snapshot");

/** Por encima de este aligeramiento (grados) se usa el polígono del mapa del explorador. */
const MAP_GEOMETRY_FROM_DEGREES = 0.002;

async function readSnapshot(relative: string): Promise<string | null> {
  try {
    return await readFile(path.join(ROOT, relative), "utf-8");
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
    throw error;
  }
}

async function readJson<T>(relative: string, schema: ZodType<T>): Promise<T | null> {
  const text = await readSnapshot(relative);
  if (text === null) return null;
  const parsed = schema.safeParse(JSON.parse(text));
  if (!parsed.success) {
    console.error(`[bosque-vivo] copia con formato inesperado en ${relative}`, parsed.error.issues);
    throw new BackendError("La copia de datos no tiene el formato esperado.", null);
  }
  return parsed.data;
}

const UNAVAILABLE = "Esta función solo está disponible en la versión con servidor.";

export const snapshotApi: BosqueVivoApi = {
  async listProjects() {
    return (await readJson("projects.json", projectSchema.array())) ?? [];
  },
  async getProject(id) {
    return (await this.listProjects()).find((project) => project.id === id) ?? null;
  },
  getGeometry(id, options) {
    const kind = (options?.simplify ?? 0) >= MAP_GEOMETRY_FROM_DEGREES ? "map" : "detail";
    return readJson(`geometry/${id}.${kind}.json`, geometrySchema);
  },
  getSeries: (id) => readJson(`series/${id}.json`, seriesSchema),
  async getDeclarations(id) {
    return (await readJson(`declarations/${id}.json`, declarationSchema.array())) ?? [];
  },
  getLatestAudit: (id) => readJson(`audit/${id}.json`, auditRunSchema),
  async chat() {
    throw new BackendError(UNAVAILABLE, null);
  },
  async traces() {
    return [];
  },
  async getReport(runId, format): Promise<ReportFile | null> {
    if (format !== "html") return null;
    const html = await readSnapshot(`reports/${runId}.html`);
    return html === null ? null : { body: html, contentType: "text/html; charset=utf-8" };
  },
};
