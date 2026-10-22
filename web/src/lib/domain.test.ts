import { describe, expect, it } from "vitest";

import type { AuditResult } from "./api/schema";
import {
  isPartialResult,
  normalizeConfidence,
  readComponents,
  readPermanence,
  readSensitivity,
  readSensor,
  toolLabel,
} from "./domain";

// Forma real que produce `IndexOutcome.components_payload()` del backend.
const realPayload: AuditResult = {
  score: 61,
  category: "Media",
  confidence: 0.72,
  confidence_label: "media",
  narrative: null,
  components: {
    permanencia: { puntaje: 70, ha_perdidas_desde_t0: 51, ha_bosque_inicial: 170, porcentaje_en_pie: 70 },
    tendencia: { puntaje: 58, pendiente_ndvi_por_anio: -0.021, tendencia_significativa: 1, p_valor: 0.012, meses_usados: 96 },
    estabilidad: { puntaje: null, motivo: "pocos meses con datos posteriores a T0" },
    _sensor: "landsat",
    _sensibilidad: { minimo: 55, maximo: 67 },
  },
};

describe("readComponents", () => {
  const components = readComponents(realPayload);

  it("devuelve los tres componentes en orden con su peso", () => {
    expect(components.map((c) => [c.key, c.weight])).toEqual([
      ["permanencia", 0.5],
      ["tendencia", 0.25],
      ["estabilidad", 0.25],
    ]);
  });

  it("lee los puntajes y los detalles legibles", () => {
    expect(components[0]!.score).toBe(70);
    expect(components[0]!.detail.map((d) => d.label)).toEqual(["Bosque en pie", "Pérdida desde T0", "Bosque inicial"]);
    expect(components[1]!.detail.find((d) => d.label === "Tendencia significativa")?.value).toBe("Sí");
  });

  it("conserva el motivo cuando no hay puntaje", () => {
    expect(components[2]!.score).toBeNull();
    expect(components[2]!.reason).toBe("pocos meses con datos posteriores a T0");
  });

  it("no falla si el backend omite componentes", () => {
    const empty = readComponents({ ...realPayload, components: {} });
    expect(empty.every((c) => c.score === null && c.detail.length === 0)).toBe(true);
  });
});

describe("otras lecturas", () => {
  it("lee el rango de sensibilidad y el sensor", () => {
    expect(readSensitivity(realPayload)).toEqual({ min: 55, max: 67 });
    expect(readSensor(realPayload)).toBe("Landsat");
  });

  it("devuelve null cuando faltan esos campos", () => {
    const bare = { ...realPayload, components: {} };
    expect(readSensitivity(bare)).toBeNull();
    expect(readSensor(bare)).toBeNull();
  });

  it("normaliza la etiqueta de confianza", () => {
    expect(normalizeConfidence("alta")).toBe("Alta");
    expect(normalizeConfidence(" MEDIA ")).toBe("Media");
    expect(normalizeConfidence("cualquier cosa")).toBe("Baja");
  });

  it("traduce herramientas conocidas y deja legibles las desconocidas", () => {
    expect(toolLabel("obtener_auditoria")).toBe("Consultó la auditoría");
    expect(toolLabel("herramienta_nueva")).toBe("herramienta nueva");
  });
});

describe("resultado parcial", () => {
  const partial: AuditResult = {
    score: null,
    category: "Insuficiente",
    confidence: 0,
    confidence_label: "baja",
    narrative: null,
    components: {
      permanencia: { puntaje: 97.4, porcentaje_en_pie: 97.4 },
      tendencia: { puntaje: null, motivo: "pocos meses con datos posteriores a T0" },
      estabilidad: { puntaje: null, motivo: "pocos meses con datos posteriores a T0" },
    },
  };

  it("lo reconoce cuando solo hay permanencia", () => {
    expect(isPartialResult(partial)).toBe(true);
    expect(readPermanence(partial)).toBe(97.4);
  });

  it("no es parcial si hay puntaje completo ni si no se midió nada", () => {
    expect(isPartialResult(realPayload)).toBe(false);
    const nothing: AuditResult = { ...partial, components: {} };
    expect(isPartialResult(nothing)).toBe(false);
    expect(readPermanence(nothing)).toBeNull();
  });
});
