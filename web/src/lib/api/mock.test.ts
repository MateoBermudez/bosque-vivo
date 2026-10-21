import { describe, expect, it } from "vitest";

import { INDEX_MODEL } from "../domain";
import { mockApi } from "./mock";
import {
  auditRunSchema,
  chatAnswerSchema,
  geometrySchema,
  projectSchema,
  seriesSchema,
  traceSchema,
} from "./schema";

// Los datos de ejemplo deben cumplir el mismo contrato que la API real; si no, la maqueta
// "miente" sobre cómo se verá el sitio con datos reales.
describe("datos de ejemplo frente al contrato de la API", () => {
  it("proyectos, geometrías, series y auditorías cumplen el esquema", async () => {
    const projects = await mockApi.listProjects();
    expect(projects.length).toBeGreaterThanOrEqual(5);
    for (const project of projects) {
      expect(() => projectSchema.parse(project)).not.toThrow();
      const geometry = await mockApi.getGeometry(project.id);
      expect(() => geometrySchema.parse(geometry)).not.toThrow();
      const series = seriesSchema.parse(await mockApi.getSeries(project.id));
      expect(series.ndvi.length).toBeGreaterThan(0);
      const audit = auditRunSchema.parse(await mockApi.getLatestAudit(project.id));
      expect(audit.project_id).toBe(project.id);
    }
  });

  it("la categoría es coherente con el puntaje y los umbrales del índice", async () => {
    for (const project of await mockApi.listProjects()) {
      const result = (await mockApi.getLatestAudit(project.id))!.result!;
      if (result.score === null) {
        expect(result.category).toBe("Insuficiente");
        continue;
      }
      const expected =
        result.score >= INDEX_MODEL.categoryHigh ? "Alta" : result.score >= INDEX_MODEL.categoryMedium ? "Media" : "Baja";
      expect(result.category).toBe(expected);
    }
  });

  it("hay un proyecto con resultado Insuficiente y datos faltantes por nubes", async () => {
    const audits = await Promise.all((await mockApi.listProjects()).map((p) => mockApi.getLatestAudit(p.id)));
    const insufficient = audits.find((a) => a?.result?.category === "Insuficiente");
    expect(insufficient).toBeDefined();
    const series = await mockApi.getSeries(insufficient!.project_id);
    expect(series!.ndvi.some((point) => point.ndvi_mean === null)).toBe(true);
  });

  it("el puntaje de permanencia coincide con el porcentaje de bosque en pie", async () => {
    for (const project of await mockApi.listProjects()) {
      const components = (await mockApi.getLatestAudit(project.id))!.result!.components;
      const permanencia = components.permanencia as { puntaje: number; porcentaje_en_pie: number };
      expect(permanencia.puntaje).toBe(permanencia.porcentaje_en_pie);
    }
  });

  it("la comparación anual marca como acreditados los años desde T0", async () => {
    const series = (await mockApi.getSeries(3))!;
    const t0Year = Number(series.t0!.slice(0, 4));
    for (const row of series.comparison) {
      expect(row.after_t0).toBe(row.year >= t0Year);
    }
  });

  it("devuelve null para proyectos que no existen", async () => {
    expect(await mockApi.getProject(999)).toBeNull();
    expect(await mockApi.getSeries(999)).toBeNull();
    expect(await mockApi.getLatestAudit(999)).toBeNull();
  });
});

describe("chat y trazas de ejemplo", () => {
  it("las respuestas del chat cumplen el esquema", async () => {
    for (const message of ["¿Cómo está Bosques del Caquetá?", "Compara dos proyectos", "¿Qué es la confianza?", "hola"]) {
      const answer = await mockApi.chat(message, "prueba");
      expect(() => chatAnswerSchema.parse(answer)).not.toThrow();
    }
  });

  it("las trazas cumplen el esquema", async () => {
    const traces = await mockApi.traces();
    expect(traces.length).toBeGreaterThan(0);
    for (const trace of traces) expect(() => traceSchema.parse(trace)).not.toThrow();
  });

  it("el reporte de ejemplo existe para una corrida y no para una inventada", async () => {
    const audit = (await mockApi.getLatestAudit(1))!;
    expect(await mockApi.getReport(audit.id, "html")).not.toBeNull();
    expect(await mockApi.getReport(audit.id, "pdf")).toBeNull();
    expect(await mockApi.getReport(987654, "html")).toBeNull();
  });
});
