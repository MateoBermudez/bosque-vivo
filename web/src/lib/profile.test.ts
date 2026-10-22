import { describe, expect, it } from "vitest";

import type { Declaration } from "./api/schema";
import { buildProfile, formatDateOnly, projectKind, registryUrl } from "./profile";

const decl = (field: string, value: string, source_document: string | null = null): Declaration => ({
  field,
  value,
  source_document,
});

describe("buildProfile", () => {
  it("reúne las declaraciones por nombre", () => {
    const profile = buildProfile([
      decl("crediting_start", "2013-11-14", "Karnik et al. (2025)"),
      decl("crediting_end", "2043-11-13"),
      decl("methodology", "VM0006"),
      decl("developer", "Comunidad X"),
      decl("processing_approach", "Georeferenced"),
      decl("geometry_source", "área de contabilidad (Georeferenced)"),
    ]);
    expect(profile).toEqual({
      creditingStart: "2013-11-14",
      creditingEnd: "2043-11-13",
      methodology: "VM0006",
      developer: "Comunidad X",
      processingApproach: "Georeferenced",
      geometrySource: "área de contabilidad (Georeferenced)",
      sourceDocument: "Karnik et al. (2025)",
    });
  });

  it("devuelve null cuando falta un dato", () => {
    const profile = buildProfile([]);
    expect(Object.values(profile).every((value) => value === null)).toBe(true);
  });
});

describe("projectKind", () => {
  it.each([
    ["Deforestación evitada (AD)", "AD"],
    ["Reforestación (ARR)", "ARR"],
    ["Manejo forestal mejorado (IFM)", "IFM"],
    ["REDD+", null],
    [null, null],
  ])("%s → %s", (type, expected) => {
    expect(projectKind(type)).toBe(expected);
  });
});

describe("registryUrl", () => {
  it("arma el enlace de Verra con el número del proyecto", () => {
    expect(registryUrl("Verra", "VCS1392")).toBe("https://registry.verra.org/app/projectDetail/VCS/1392");
    expect(registryUrl("verra", "VCS-0001")).toBe("https://registry.verra.org/app/projectDetail/VCS/1");
  });

  it("no inventa enlaces para otros registros", () => {
    expect(registryUrl("EcoRegistry", "ER55")).toBeNull();
    expect(registryUrl("Gold Standard", "GS3025")).toBeNull();
    expect(registryUrl("Verra", "algo raro")).toBeNull();
  });
});

describe("formatDateOnly", () => {
  it("formatea sin correrse de día por la zona horaria", () => {
    expect(formatDateOnly("2013-11-14")).toMatch(/14.*nov.*2013/);
    expect(formatDateOnly("2018-01-01")).toMatch(/1.*ene.*2018/);
  });

  it("devuelve el texto original si no es una fecha", () => {
    expect(formatDateOnly("no es fecha")).toBe("no es fecha");
  });
});
