import type { AuditResult, Category } from "./api/schema";

/** Pesos y umbrales del índice v0 (ver docs/methodology/indice-v0.md del backend). */
export const INDEX_MODEL = {
  version: "v0",
  weights: { permanencia: 0.5, tendencia: 0.25, estabilidad: 0.25 },
  categoryHigh: 75,
  categoryMedium: 50,
  confidenceHigh: 0.7,
  confidenceMedium: 0.4,
} as const;

export const SAMPLE_NOTICE = "Datos ilustrativos, no corresponden a proyectos reales evaluados";

export const categoryBg: Record<Category, string> = {
  Alta: "bg-cat-alta",
  Media: "bg-cat-media",
  Baja: "bg-cat-baja",
  Insuficiente: "bg-cat-insuficiente",
};

export const categoryFill: Record<Category, string> = {
  Alta: "var(--cat-alta)",
  Media: "var(--cat-media)",
  Baja: "var(--cat-baja)",
  Insuficiente: "var(--cat-insuficiente)",
};

/** Color literal para MapLibre, que no resuelve variables CSS. */
export const categoryHex: Record<Category, string> = {
  Alta: "#7ccf4a",
  Media: "#e3b93c",
  Baja: "#e0703a",
  Insuficiente: "#9a9d96",
};

export type ConfidenceLabel = "Alta" | "Media" | "Baja";

export function normalizeConfidence(label: string): ConfidenceLabel {
  const value = label.trim().toLowerCase();
  if (value === "alta") return "Alta";
  if (value === "media") return "Media";
  return "Baja";
}

export function sensorLabel(sensor: string): string {
  if (sensor === "s2") return "Sentinel-2";
  if (sensor === "landsat") return "Landsat";
  if (sensor === "modis") return "MODIS (250 m)";
  return sensor;
}

export type ComponentKey = keyof typeof INDEX_MODEL.weights;

export interface ComponentView {
  key: ComponentKey;
  label: string;
  weight: number;
  score: number | null;
  reason: string | null;
  detail: { label: string; value: string }[];
}

const COMPONENT_LABELS: Record<ComponentKey, string> = {
  permanencia: "Permanencia forestal",
  tendencia: "Tendencia de vigor",
  estabilidad: "Estabilidad",
};

const number = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 });

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function describeDetail(key: ComponentKey, raw: Record<string, unknown>) {
  const out: { label: string; value: string }[] = [];
  const add = (label: string, value: unknown, unit = "") => {
    const n = asNumber(value);
    if (n !== null) out.push({ label, value: `${number.format(n)}${unit}` });
  };
  if (key === "permanencia") {
    add("Bosque en pie", raw.porcentaje_en_pie, " %");
    add("Pérdida desde T0", raw.ha_perdidas_desde_t0, " ha");
    add("Bosque inicial", raw.ha_bosque_inicial, " ha");
  } else if (key === "tendencia") {
    add("Pendiente del NDVI", raw.pendiente_ndvi_por_anio, " por año");
    add("Meses analizados", raw.meses_usados);
    if (asNumber(raw.tendencia_significativa) !== null) {
      out.push({
        label: "Tendencia significativa",
        value: raw.tendencia_significativa ? "Sí" : "No",
      });
    }
  } else {
    add("Mayor caída del NDVI", raw.caida_maxima_ndvi);
    if (typeof raw.fecha_caida === "string") out.push({ label: "Fecha de la caída", value: raw.fecha_caida });
  }
  return out;
}

/** Convierte el JSON libre de `components` en filas listas para mostrar. */
export function readComponents(result: AuditResult): ComponentView[] {
  return (Object.keys(INDEX_MODEL.weights) as ComponentKey[]).map((key) => {
    const raw = asRecord(result.components[key]);
    const reason = typeof raw.motivo === "string" ? raw.motivo : null;
    return {
      key,
      label: COMPONENT_LABELS[key],
      weight: INDEX_MODEL.weights[key],
      score: asNumber(raw.puntaje),
      reason,
      detail: describeDetail(key, raw),
    };
  });
}

/** Permanencia forestal medida (0-100), o `null` si no se pudo calcular. */
export function readPermanence(result: AuditResult): number | null {
  return readComponents(result).find((component) => component.key === "permanencia")?.score ?? null;
}

/** Sin puntaje global pero con al menos un componente medido (p. ej. solo la permanencia de Hansen). */
export function isPartialResult(result: AuditResult): boolean {
  return result.score === null && readComponents(result).some((component) => component.score !== null);
}

/** Rango del puntaje al mover cada peso ±10 pp (campo `_sensibilidad`). */
export function readSensitivity(result: AuditResult): { min: number; max: number } | null {
  const raw = asRecord(result.components._sensibilidad);
  const min = asNumber(raw.minimo);
  const max = asNumber(raw.maximo);
  return min !== null && max !== null ? { min, max } : null;
}

/** Sensor que se usó para calcular el índice ("s2" o "landsat"); no se mezclan. */
export function readSensorKey(result: AuditResult): string | null {
  const value = result.components._sensor;
  return typeof value === "string" ? value : null;
}

export function readSensor(result: AuditResult): string | null {
  const key = readSensorKey(result);
  return key === null ? null : sensorLabel(key);
}

const TOOL_LABELS: Record<string, string> = {
  buscar_proyecto: "Buscó el proyecto",
  obtener_auditoria: "Consultó la auditoría",
  obtener_serie_ndvi: "Revisó la serie NDVI",
  obtener_perdida_anual: "Revisó la pérdida anual",
  comparar_periodos: "Comparó periodos",
  ver_imagenes: "Miró imágenes satelitales",
  buscar_conocimiento: "Consultó la base de conocimiento",
  analizar_foto_usuario: "Analizó una foto",
  explicar_indice: "Explicó el índice",
  solicitar_calculo: "Pidió un cálculo",
  generar_reporte: "Generó un reporte",
};

export function toolLabel(tool: string): string {
  return TOOL_LABELS[tool] ?? tool.replaceAll("_", " ");
}

export function queryClassLabel(value: string): string {
  return value === "profunda" ? "Profunda" : "Rápida";
}

export function roleLabel(value: string): string {
  if (value === "auditor") return "Auditor";
  if (value === "comunidad") return "Comunidad";
  return value;
}
