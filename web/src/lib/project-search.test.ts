import { describe, expect, it } from "vitest";

import { filterProjects, normalizeText, type PickerProject } from "./project-search";

const project = (id: number, name: string): PickerProject => ({ id, name, country: "Colombia", area_ha: 1000 });

const PROJECTS = [
  project(1, "Carmen del Darien (CDD) REDD+ Project"),
  project(2, "The Choco-Darien Conservation Corridor REDD Project"),
  project(3, "Concosta REDD+ Project"),
  project(4, "REDD+ Pazcifico"),
  project(5, "Proyecto REDD+ Pazcifico Sur"),
  project(6, "Mutatá REDD+ Project"),
];

describe("normalizeText", () => {
  it("quita tildes, signos y mayúsculas", () => {
    expect(normalizeText("  Mutatá REDD+  ")).toBe("mutata redd");
  });
});

describe("filterProjects", () => {
  it("encuentra con o sin tildes", () => {
    expect(filterProjects(PROJECTS, "mutata").map((p) => p.id)).toEqual([6]);
    expect(filterProjects(PROJECTS, "Mutatá").map((p) => p.id)).toEqual([6]);
  });

  it("exige todas las palabras escritas", () => {
    expect(filterProjects(PROJECTS, "darien corridor").map((p) => p.id)).toEqual([2]);
  });

  it("pone primero los que empiezan por lo escrito", () => {
    expect(filterProjects(PROJECTS, "carmen").map((p) => p.id)).toEqual([1]);
    expect(filterProjects(PROJECTS, "pazcifico").map((p) => p.id).sort()).toEqual([4, 5]);
    const mixed = [project(7, "Reserva Concosta Norte"), project(3, "Concosta REDD+ Project")];
    expect(filterProjects(mixed, "concosta").map((p) => p.id)).toEqual([3, 7]);
  });

  it("sin texto devuelve los primeros por orden alfabético, con tope", () => {
    const first = filterProjects(PROJECTS, "", 3);
    expect(first).toHaveLength(3);
    expect(first.map((p) => p.name)).toEqual([...first.map((p) => p.name)].sort((a, b) => a.localeCompare(b, "es")));
  });

  it("devuelve una lista vacía si nada coincide", () => {
    expect(filterProjects(PROJECTS, "nube fantasma")).toEqual([]);
  });
});
