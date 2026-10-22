// Formas de las respuestas de la API de Bosque Vivo (backend FastAPI).
// Se validan en el servidor: si el backend cambia, el sitio falla con un mensaje claro
// en vez de renderizar datos incorrectos.
import { z } from "zod";

export const CATEGORIES = ["Alta", "Media", "Baja", "Insuficiente"] as const;
export const categorySchema = z.enum(CATEGORIES);
export type Category = z.infer<typeof categorySchema>;

export const projectSchema = z.object({
  id: z.number().int(),
  source_registry: z.string(),
  registry_id: z.string(),
  name: z.string(),
  country: z.string().nullable(),
  project_type: z.string().nullable(),
  start_year: z.number().int().nullable(),
  area_ha: z.number().nullable(),
});
export type Project = z.infer<typeof projectSchema>;

const position = z.array(z.number()).min(2);
const polygonCoordinates = z.array(z.array(position));

export const geometrySchema = z.object({
  type: z.literal("Feature"),
  properties: z.record(z.string(), z.unknown()),
  geometry: z.discriminatedUnion("type", [
    z.object({ type: z.literal("Polygon"), coordinates: polygonCoordinates }),
    z.object({ type: z.literal("MultiPolygon"), coordinates: z.array(polygonCoordinates) }),
  ]),
});
export type ProjectGeometry = z.infer<typeof geometrySchema>;

export const ndviPointSchema = z.object({
  period: z.string(),
  sensor: z.string(),
  ndvi_mean: z.number().nullable(),
  valid_fraction: z.number(),
  scene_count: z.number(),
});
export type NdviPoint = z.infer<typeof ndviPointSchema>;

export const declarationSchema = z.object({
  field: z.string(),
  value: z.string(),
  source_document: z.string().nullable(),
});
export type Declaration = z.infer<typeof declarationSchema>;

export const comparisonRowSchema = z.object({
  year: z.number().int(),
  after_t0: z.boolean(),
  ndvi_mean: z.number().nullable(),
  loss_ha: z.number(),
  declared_note: z.string(),
});
export type ComparisonRow = z.infer<typeof comparisonRowSchema>;

export const seriesSchema = z.object({
  t0: z.string().nullable(),
  ndvi: z.array(ndviPointSchema),
  loss: z.array(z.object({ year: z.number().int(), ha_lost: z.number() })),
  comparison: z.array(comparisonRowSchema),
});
export type Series = z.infer<typeof seriesSchema>;

export const auditResultSchema = z.object({
  score: z.number().nullable(),
  category: categorySchema,
  components: z.record(z.string(), z.unknown()),
  confidence: z.number(),
  confidence_label: z.string(),
  narrative: z.string().nullable(),
});
export type AuditResult = z.infer<typeof auditResultSchema>;

export const auditRunSchema = z.object({
  id: z.number().int(),
  project_id: z.number().int(),
  status: z.string(),
  index_version: z.string(),
  git_sha: z.string().nullable(),
  dataset_versions: z.record(z.string(), z.unknown()),
  created_at: z.string(),
  result: auditResultSchema.nullable(),
});
export type AuditRun = z.infer<typeof auditRunSchema>;

export const chatAnswerSchema = z.object({
  answer: z.string(),
  evidence_ids: z.array(z.string()),
  tools_called: z.array(z.string()),
  used_fallback: z.boolean(),
  query_class: z.string(),
  run_id: z.number().int(),
});
export type ChatAnswer = z.infer<typeof chatAnswerSchema>;

export const traceSchema = z.object({
  id: z.number().int(),
  role: z.string(),
  query_class: z.string(),
  query: z.string(),
  answer: z.string().nullable(),
  model: z.string().nullable(),
  prompt_version: z.string(),
  used_fallback: z.boolean(),
  validator_passed: z.boolean().nullable(),
  latency_ms: z.number().nullable(),
  tools: z.array(z.string()),
});
export type Trace = z.infer<typeof traceSchema>;

/** Cuerpo que acepta POST /api/v1/chat (límites iguales a los del backend). */
export const chatRequestSchema = z.object({
  message: z.string().trim().min(1).max(2000),
  session_ref: z.string().min(1).max(60).default("web"),
});
export type ChatRequest = z.infer<typeof chatRequestSchema>;
