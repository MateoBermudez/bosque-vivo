// Datos ilustrativos con la MISMA forma que devuelve la API real (ver schema.ts).
// Sirven para desarrollar el sitio sin backend y para las demos sin conexión.
// No corresponden a proyectos reales evaluados.
import { INDEX_MODEL, SAMPLE_NOTICE } from "../domain";
import type {
  AuditRun,
  Category,
  ChatAnswer,
  ComparisonRow,
  Declaration,
  NdviPoint,
  Project,
  ProjectGeometry,
  Series,
  Trace,
} from "./schema";
import type { BosqueVivoApi, ReportFile } from "./types";

const GIT_SHA = "a3f9c1e";
const CREATED_AT = "2026-10-18T14:12:00Z";
const DATASET_VERSIONS = {
  sentinel2: "COPERNICUS/S2_SR_HARMONIZED",
  cloud_score: "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED",
  landsat: "LANDSAT/LT05/C02/T1_L2,LANDSAT/LE07/C02/T1_L2,LANDSAT/LC08/C02/T1_L2,LANDSAT/LC09/C02/T1_L2",
  hansen: "UMD/hansen/global_forest_change_2024_v1_12",
};

interface Spec {
  project: Project;
  center: [number, number];
  radius: number;
  ndvi: { base: number; drift: number; drop: number; dropFrom: number; startYear: number; cloudy?: boolean };
  t0: string;
  loss: Record<number, number>;
  /** Puntajes objetivo por componente. `null` = sin datos suficientes. */
  targets: { permanencia: number; tendencia: number | null; estabilidad: number | null };
  confidence: number;
  narrative: string;
}

const SPECS: Spec[] = [
  {
    project: { id: 1, source_registry: "Verra", registry_id: "VCS-0001", name: "Selva del Guaviare", country: "Colombia", project_type: "REDD+", start_year: 2016, area_ha: 48250 },
    center: [-72.6, 2.4],
    radius: 0.9,
    ndvi: { base: 0.84, drift: 0.0005, drop: 0.02, dropFrom: 2021, startYear: 2010 },
    t0: "2016-01-01",
    loss: { 2016: 42, 2017: 38, 2018: 51, 2019: 30, 2020: 28, 2021: 64, 2022: 45, 2023: 33, 2024: 29 },
    targets: { permanencia: 92, tendencia: 78, estabilidad: 82 },
    confidence: 0.88,
    narrative:
      "Desde que empezó el proyecto, el bosque se ha mantenido casi igual. Las imágenes satelitales muestran poca pérdida y un verdor estable. Lo que declara el proyecto y lo que se observa desde el satélite corresponden bien.",
  },
  {
    project: { id: 2, source_registry: "Cercarbono", registry_id: "CCB-0207", name: "Corredor Andino Las Nubes", country: "Colombia", project_type: "Reforestación (ARR)", start_year: 2018, area_ha: 3120 },
    center: [-75.6, 5.9],
    radius: 0.45,
    ndvi: { base: 0.48, drift: 0.012, drop: 0, dropFrom: 2099, startYear: 2012 },
    t0: "2018-01-01",
    loss: { 2018: 6, 2019: 9, 2020: 4, 2021: 12, 2022: 8, 2023: 5, 2024: 7 },
    targets: { permanencia: 70, tendencia: 58, estabilidad: 46 },
    confidence: 0.72,
    narrative:
      "Los árboles plantados están creciendo, pero más despacio de lo que se declaró. En parte del área el verdor aumenta y en otra se mantiene igual. La correspondencia observada es parcial.",
  },
  {
    project: { id: 3, source_registry: "Verra", registry_id: "VCS-0315", name: "Bosques del Caquetá", country: "Colombia", project_type: "REDD+", start_year: 2014, area_ha: 92400 },
    center: [-74.4, 0.9],
    radius: 1.1,
    ndvi: { base: 0.83, drift: -0.002, drop: 0.11, dropFrom: 2018, startYear: 2010 },
    t0: "2014-01-01",
    loss: { 2014: 180, 2015: 210, 2016: 260, 2017: 540, 2018: 1320, 2019: 1810, 2020: 1460, 2021: 1290, 2022: 980, 2023: 870, 2024: 1120 },
    targets: { permanencia: 31, tendencia: 35, estabilidad: 39 },
    confidence: 0.84,
    narrative:
      "Desde 2018 se observa una pérdida de bosque mayor a la esperada y el verdor viene bajando. Son señales que conviene revisar en terreno con la comunidad y el desarrollador del proyecto.",
  },
  {
    project: { id: 4, source_registry: "Gold Standard", registry_id: "GS-1188", name: "Manglares del Pacífico", country: "Ecuador", project_type: "Conservación", start_year: 2019, area_ha: 7800 },
    center: [-79.6, 1.0],
    radius: 0.5,
    ndvi: { base: 0.7, drift: 0.001, drop: 0.03, dropFrom: 2023, startYear: 2014, cloudy: true },
    t0: "2019-01-01",
    loss: { 2019: 12, 2020: 18, 2021: 9, 2022: 22, 2023: 35, 2024: 28 },
    targets: { permanencia: 90, tendencia: null, estabilidad: null },
    confidence: 0.31,
    narrative:
      "La zona tiene muchas nubes casi todo el año, así que hay pocas imágenes útiles. Por ahora no hay datos suficientes para calcular el índice con seguridad.",
  },
  {
    project: { id: 5, source_registry: "Verra", registry_id: "VCS-0942", name: "Amazonía Madre de Dios", country: "Perú", project_type: "REDD+", start_year: 2012, area_ha: 61300 },
    center: [-70.4, -2.6],
    radius: 1.0,
    ndvi: { base: 0.86, drift: -0.0008, drop: 0.04, dropFrom: 2019, startYear: 2010 },
    t0: "2012-01-01",
    loss: { 2012: 80, 2014: 95, 2016: 110, 2018: 160, 2019: 340, 2020: 420, 2021: 380, 2022: 290, 2023: 260, 2024: 240 },
    targets: { permanencia: 62, tendencia: 51, estabilidad: 56 },
    confidence: 0.79,
    narrative:
      "El bosque se mantiene en su mayoría, aunque desde 2019 la pérdida es un poco mayor de lo esperado. La correspondencia observada es intermedia.",
  },
  {
    project: { id: 6, source_registry: "Cercarbono", registry_id: "CCB-0411", name: "Sabana Arbolada del Meta", country: "Colombia", project_type: "Reforestación (ARR)", start_year: 2021, area_ha: 1450 },
    center: [-71.9, 4.5],
    radius: 0.4,
    ndvi: { base: 0.42, drift: 0.006, drop: 0.05, dropFrom: 2023, startYear: 2016 },
    t0: "2021-01-01",
    loss: { 2021: 3, 2022: 5, 2023: 14, 2024: 11 },
    targets: { permanencia: 55, tendencia: 22, estabilidad: 48 },
    confidence: 0.6,
    narrative:
      "La plantación es reciente. Hasta ahora el verdor no ha aumentado como se esperaba y en 2023 hubo una pérdida puntual. Es pronto para conclusiones firmes, pero las señales piden seguimiento.",
  },
];

/** Ruido determinista para que los datos de ejemplo no cambien entre recargas. */
function noise(a: number, b: number, salt: number): number {
  const x = Math.sin(a * 127.1 + b * 311.7 + salt * 74.7) * 43758.5453;
  return x - Math.floor(x);
}

function polygon(center: [number, number], radius: number): ProjectGeometry["geometry"] {
  const points: number[][] = [];
  const sides = 8;
  for (let i = 0; i < sides; i++) {
    const angle = (i / sides) * Math.PI * 2;
    const r = radius * (0.72 + noise(i, center[0], 3) * 0.5);
    points.push([+(center[0] + Math.cos(angle) * r).toFixed(4), +(center[1] + Math.sin(angle) * r * 0.8).toFixed(4)]);
  }
  points.push(points[0]!);
  return { type: "Polygon", coordinates: [points] };
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

function buildNdvi(spec: Spec): NdviPoint[] {
  const { base, drift, drop, dropFrom, startYear, cloudy } = spec.ndvi;
  const points: NdviPoint[] = [];
  for (const sensor of ["landsat", "s2"] as const) {
    const from = sensor === "s2" ? Math.max(2017, startYear) : startYear;
    for (let year = from; year <= 2025; year++) {
      for (let month = 1; month <= 12; month++) {
        if (year === 2025 && month > 9) break;
        const t = year - startYear + (month - 1) / 12;
        const seasonal = 0.03 * Math.sin(((month - 1) / 12) * Math.PI * 2);
        const loss = year >= dropFrom ? drop * Math.min(1, (year - dropFrom + month / 12) / 3) : 0;
        const wobble = (noise(year, month, sensor === "s2" ? 1 : 2) - 0.5) * 0.03;
        const sensorOffset = sensor === "s2" ? 0.012 : 0;
        const valid = cloudy
          ? 0.05 + noise(year, month, 5) * 0.28
          : 0.55 + noise(year, month, 6) * 0.4;
        const missing = cloudy && valid < 0.1;
        points.push({
          period: `${year}-${pad(month)}-01`,
          sensor,
          ndvi_mean: missing ? null : +Math.min(0.95, Math.max(0.15, base + drift * t + seasonal - loss + wobble + sensorOffset)).toFixed(3),
          valid_fraction: +valid.toFixed(2),
          scene_count: sensor === "s2" ? 4 + Math.floor(noise(year, month, 7) * 6) : 1 + Math.floor(noise(year, month, 8) * 3),
        });
      }
    }
  }
  return points.sort((a, b) => a.period.localeCompare(b.period) || a.sensor.localeCompare(b.sensor));
}

function buildComparison(spec: Spec, ndvi: NdviPoint[]): ComparisonRow[] {
  const t0 = new Date(`${spec.t0}T00:00:00Z`);
  const byYear = new Map<number, number[]>();
  for (const point of ndvi) {
    if (point.sensor !== "landsat" || point.ndvi_mean === null) continue;
    const year = Number(point.period.slice(0, 4));
    byYear.set(year, [...(byYear.get(year) ?? []), point.ndvi_mean]);
  }
  const years = [...new Set([...byYear.keys(), ...Object.keys(spec.loss).map(Number)])].sort((a, b) => a - b);
  return years.map((year) => {
    const values = byYear.get(year) ?? [];
    const after = new Date(Date.UTC(year, 11, 31)) >= t0;
    return {
      year,
      after_t0: after,
      ndvi_mean: values.length ? +(values.reduce((s, v) => s + v, 0) / values.length).toFixed(4) : null,
      loss_ha: +(spec.loss[year] ?? 0).toFixed(2),
      declared_note: after ? "acreditado" : "previo a la acreditación",
    };
  });
}

function categorize(score: number): Category {
  if (score >= INDEX_MODEL.categoryHigh) return "Alta";
  if (score >= INDEX_MODEL.categoryMedium) return "Media";
  return "Baja";
}

function confidenceLabel(value: number): string {
  if (value >= INDEX_MODEL.confidenceHigh) return "alta";
  if (value >= INDEX_MODEL.confidenceMedium) return "media";
  return "baja";
}

const INSUFFICIENT_REASON = "pocos meses con datos posteriores a T0";

function buildAudit(spec: Spec): AuditRun {
  const { targets } = spec;
  const t0Year = Number(spec.t0.slice(0, 4));
  const lostSinceT0 = Object.entries(spec.loss)
    .filter(([year]) => Number(year) >= t0Year)
    .reduce((sum, [, ha]) => sum + ha, 0);
  const baseline = lostSinceT0 / (1 - targets.permanencia / 100);

  const permanencia = {
    puntaje: targets.permanencia,
    ha_perdidas_desde_t0: +lostSinceT0.toFixed(2),
    ha_bosque_inicial: +baseline.toFixed(2),
    porcentaje_en_pie: targets.permanencia,
  };
  const tendencia =
    targets.tendencia === null
      ? { puntaje: null, motivo: INSUFFICIENT_REASON }
      : {
          puntaje: targets.tendencia,
          pendiente_ndvi_por_anio: +(0.05 * (targets.tendencia / 100 - 1)).toFixed(4),
          tendencia_significativa: targets.tendencia < 70 ? 1 : 0,
          p_valor: targets.tendencia < 70 ? 0.012 : 0.31,
          meses_usados: 96,
        };
  const estabilidad =
    targets.estabilidad === null
      ? { puntaje: null, motivo: INSUFFICIENT_REASON }
      : {
          puntaje: targets.estabilidad,
          caida_maxima_ndvi: +(0.05 + 0.25 * (1 - targets.estabilidad / 100)).toFixed(4),
          fecha_caida: `${Math.min(2025, Math.max(t0Year + 1, spec.ndvi.dropFrom))}-06-01`,
        };

  const parts = [
    { score: targets.permanencia, weight: INDEX_MODEL.weights.permanencia },
    ...(targets.tendencia === null ? [] : [{ score: targets.tendencia, weight: INDEX_MODEL.weights.tendencia }]),
    ...(targets.estabilidad === null ? [] : [{ score: targets.estabilidad, weight: INDEX_MODEL.weights.estabilidad }]),
  ];
  const totalWeight = parts.reduce((s, p) => s + p.weight, 0);
  const weighted = parts.reduce((s, p) => s + p.score * p.weight, 0) / totalWeight;
  const insufficient = targets.tendencia === null || spec.confidence < 0.3 + 0.01;
  const score = insufficient ? null : +weighted.toFixed(1);

  return {
    id: spec.project.id * 100 + 1,
    project_id: spec.project.id,
    status: "completed",
    index_version: INDEX_MODEL.version,
    git_sha: GIT_SHA,
    dataset_versions: DATASET_VERSIONS,
    created_at: CREATED_AT,
    result: {
      score,
      category: score === null ? "Insuficiente" : categorize(score),
      components: {
        permanencia,
        tendencia,
        estabilidad,
        _sensor: "landsat",
        ...(score === null ? {} : { _sensibilidad: { minimo: +(score - 6).toFixed(1), maximo: +Math.min(100, score + 6).toFixed(1) } }),
      },
      confidence: spec.confidence,
      confidence_label: confidenceLabel(spec.confidence),
      narrative: spec.narrative,
    },
  };
}

const PROJECTS = SPECS.map((s) => s.project);
const GEOMETRIES = new Map<number, ProjectGeometry>(
  SPECS.map((s) => [
    s.project.id,
    { type: "Feature", properties: { id: s.project.id, name: s.project.name }, geometry: polygon(s.center, s.radius) },
  ]),
);
const SERIES = new Map<number, Series>(
  SPECS.map((s) => {
    const ndvi = buildNdvi(s);
    return [
      s.project.id,
      {
        t0: s.t0,
        ndvi,
        loss: Object.entries(s.loss).map(([year, ha]) => ({ year: Number(year), ha_lost: ha })),
        comparison: buildComparison(s, ndvi),
      },
    ];
  }),
);
const DECLARATIONS = new Map<number, Declaration[]>(
  SPECS.map((s) => {
    const source = "Datos ilustrativos";
    const endYear = Number(s.t0.slice(0, 4)) + 30;
    return [
      s.project.id,
      [
        { field: "crediting_start", value: s.t0, source_document: source },
        { field: "crediting_end", value: `${endYear}-12-31`, source_document: source },
        { field: "methodology", value: "VM0007 (ejemplo)", source_document: source },
        { field: "developer", value: "Desarrollador de ejemplo", source_document: source },
        { field: "processing_approach", value: "Official", source_document: source },
        { field: "geometry_source", value: "área del proyecto (Official)", source_document: source },
      ],
    ];
  }),
);
const AUDITS = new Map<number, AuditRun>(SPECS.map((s) => [s.project.id, buildAudit(s)]));

const MOCK_TRACES: Trace[] = [
  { id: 5, role: "auditor", query_class: "profunda", query: "Compara Bosques del Caquetá con Selva del Guaviare", answer: "Bosques del Caquetá tiene un índice de 34,8 (Baja) y Selva del Guaviare de 86,0 (Alta). La mayor diferencia está en la permanencia forestal.", model: "modelo-de-ejemplo", prompt_version: "auditor-v1", used_fallback: false, validator_passed: true, latency_ms: 6420, tools: ["obtener_auditoria", "obtener_auditoria", "comparar_periodos"] },
  { id: 4, role: "comunidad", query_class: "rapida", query: "¿Mi finca está dentro de algún proyecto?", answer: "Sí. Su ubicación está dentro de Corredor Andino Las Nubes.", model: "modelo-de-ejemplo", prompt_version: "comunidad-v1", used_fallback: false, validator_passed: true, latency_ms: 1840, tools: ["buscar_proyecto"] },
  { id: 3, role: "auditor", query_class: "rapida", query: "¿Qué es el NDVI?", answer: "Es un número entre -1 y 1 que indica qué tan verde y sana está la vegetación.", model: "modelo-de-ejemplo", prompt_version: "auditor-v1", used_fallback: false, validator_passed: true, latency_ms: 1210, tools: ["buscar_conocimiento"] },
  { id: 2, role: "auditor", query_class: "profunda", query: "¿Por qué Manglares del Pacífico no tiene índice?", answer: "Hay muy pocas imágenes útiles por las nubes, así que no hay datos suficientes para calcular el índice.", model: "modelo-de-ejemplo", prompt_version: "auditor-v1", used_fallback: false, validator_passed: false, latency_ms: 7980, tools: ["obtener_auditoria", "obtener_serie_ndvi"] },
  { id: 1, role: "comunidad", query_class: "profunda", query: "(foto) ¿Esto es tala?", answer: "La foto no permite una conclusión. ¿Puede compartir también su ubicación?", model: "modelo-de-ejemplo", prompt_version: "comunidad-v1", used_fallback: true, validator_passed: null, latency_ms: 3150, tools: ["analizar_foto_usuario"] },
];

let chatRun = 100;

function findProject(message: string): Project | undefined {
  const text = message.toLowerCase();
  return PROJECTS.find((p) => p.name.toLowerCase().split(" ").filter((w) => w.length > 4).some((w) => text.includes(w)));
}

function describeAudit(project: Project): string {
  const audit = AUDITS.get(project.id)!;
  const result = audit.result!;
  const score = result.score === null ? "sin calcular" : String(result.score).replace(".", ",");
  return `Para ${project.name} el índice es ${score} (${result.category}). ${result.narrative}`;
}

function mockChat(message: string): ChatAnswer {
  const text = message.toLowerCase();
  chatRun += 1;
  const base = { used_fallback: false, run_id: chatRun };
  const deep = /(compar|analiz|imagen|foto|sat[eé]lite)/.test(text);
  if (text.includes("compar")) {
    const a = AUDITS.get(3)!.result!;
    const b = AUDITS.get(1)!.result!;
    return {
      ...base,
      query_class: "profunda",
      answer: `Bosques del Caquetá tiene un índice de ${String(a.score).replace(".", ",")} (${a.category}) y Selva del Guaviare de ${String(b.score).replace(".", ",")} (${b.category}). La mayor diferencia está en la permanencia forestal: en Caquetá ha quedado en pie una parte mucho menor del bosque inicial.`,
      evidence_ids: ["ev_1_mock0003", "ev_2_mock0001"],
      tools_called: ["obtener_auditoria", "obtener_auditoria", "comparar_periodos"],
    };
  }
  if (text.includes("confianza")) {
    return {
      ...base,
      query_class: "rapida",
      answer: "La confianza indica qué tan seguros estamos del índice, no si el proyecto es bueno o malo. Depende de cuántas imágenes útiles hubo (sin nubes) y de la fracción de píxeles válidos. Si es baja, mira el resultado con cautela.",
      evidence_ids: ["ev_1_mockkb01"],
      tools_called: ["buscar_conocimiento"],
    };
  }
  const project = findProject(message);
  if (project) {
    return {
      ...base,
      query_class: deep ? "profunda" : "rapida",
      answer: describeAudit(project),
      evidence_ids: [`ev_1_mock${project.id.toString().padStart(4, "0")}`],
      tools_called: ["buscar_proyecto", "obtener_auditoria"],
    };
  }
  return {
    ...base,
    query_class: "rapida",
    answer: "Puedo explicarte el índice de un proyecto, compararlo con otro o aclarar términos como NDVI o confianza. Prueba con el nombre de un proyecto, por ejemplo: ¿por qué el índice de Bosques del Caquetá es bajo?",
    evidence_ids: [],
    tools_called: [],
  };
}

function mockReport(runId: number): ReportFile | null {
  const audit = [...AUDITS.values()].find((a) => a.id === runId);
  const project = audit && PROJECTS.find((p) => p.id === audit.project_id);
  if (!audit?.result || !project) return null;
  const html = `<!doctype html><html lang="es-CO"><meta charset="utf-8"><title>Reporte ${runId}</title>
<body style="font-family:system-ui;max-width:42rem;margin:2rem auto;padding:0 1rem">
<h1>${project.name}</h1>
<p>${project.source_registry} · ${project.registry_id}</p>
<p><b>Índice:</b> ${audit.result.score ?? "no calculable"} (${audit.result.category}) · <b>Confianza:</b> ${audit.result.confidence_label}</p>
<p>${audit.result.narrative ?? ""}</p>
<p><small>Versión del índice ${audit.index_version} · código ${audit.git_sha} · ${audit.created_at}<br>${SAMPLE_NOTICE}.</small></p>
</body></html>`;
  return { body: html, contentType: "text/html; charset=utf-8" };
}

export const mockApi: BosqueVivoApi = {
  listProjects: async () => PROJECTS,
  getProject: async (id) => PROJECTS.find((p) => p.id === id) ?? null,
  getGeometry: async (id) => GEOMETRIES.get(id) ?? null,
  getSeries: async (id) => SERIES.get(id) ?? null,
  getDeclarations: async (id) => DECLARATIONS.get(id) ?? [],
  getLatestAudit: async (id) => AUDITS.get(id) ?? null,
  chat: async (message) => {
    await new Promise((resolve) => setTimeout(resolve, 700));
    return mockChat(message);
  },
  traces: async (limit = 50) => MOCK_TRACES.slice(0, limit),
  getReport: async (runId, format) => (format === "html" ? mockReport(runId) : null),
};
