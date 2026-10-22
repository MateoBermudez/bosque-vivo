import "server-only";

import type { ZodType } from "zod";

import {
  auditRunSchema,
  chatAnswerSchema,
  declarationSchema,
  geometrySchema,
  projectSchema,
  seriesSchema,
  traceSchema,
} from "./schema";
import type { BosqueVivoApi, ReportFile } from "./types";

export class BackendError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
  ) {
    super(message);
    this.name = "BackendError";
  }
}

const API_PREFIX = "/api/v1";

function baseUrl(): string {
  return (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
}

type RequestOptions = {
  admin?: boolean;
  method?: "GET" | "POST";
  body?: unknown;
  timeoutMs?: number;
  /** Estados HTTP que significan "no existe" y se devuelven como `null`. */
  nullOn?: number[];
};

function buildHeaders(options: RequestOptions): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.admin) {
    const token = process.env.ADMIN_TOKEN;
    if (!token) {
      throw new BackendError(
        "El sitio no tiene configurado ADMIN_TOKEN para consultar esta información.",
        null,
      );
    }
    headers["X-Admin-Token"] = token;
  }
  return headers;
}

async function send(path: string, options: RequestOptions): Promise<Response | null> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, {
      method: options.method ?? "GET",
      headers: buildHeaders(options),
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      cache: "no-store",
      signal: AbortSignal.timeout(options.timeoutMs ?? 30_000),
    });
  } catch (error) {
    if (error instanceof BackendError) throw error;
    throw new BackendError(
      "No pudimos conectar con el servidor de Bosque Vivo. Verifica que la API esté encendida.",
      null,
    );
  }
  if (options.nullOn?.includes(response.status)) return null;
  if (!response.ok) {
    let detail = "";
    try {
      const payload: unknown = await response.json();
      if (payload && typeof payload === "object" && "detail" in payload) {
        const value = (payload as { detail: unknown }).detail;
        if (typeof value === "string") detail = value;
      }
    } catch {
      // El cuerpo no era JSON: se usa el mensaje genérico.
    }
    throw new BackendError(detail || `El servidor respondió con el estado ${response.status}.`, response.status);
  }
  return response;
}

async function getJson<T>(path: string, schema: ZodType<T>, options: RequestOptions = {}): Promise<T | null> {
  const response = await send(path, options);
  if (response === null) return null;
  const parsed = schema.safeParse(await response.json());
  if (!parsed.success) {
    console.error(`[bosque-vivo] respuesta inesperada en ${path}`, parsed.error.issues);
    throw new BackendError("La respuesta del servidor no tiene el formato esperado.", null);
  }
  return parsed.data;
}

async function requireJson<T>(path: string, schema: ZodType<T>, options: RequestOptions = {}): Promise<T> {
  const value = await getJson(path, schema, options);
  if (value === null) throw new BackendError("No encontramos lo que buscabas.", 404);
  return value;
}

export const liveApi: BosqueVivoApi = {
  listProjects: () => requireJson(`${API_PREFIX}/projects?limit=200`, projectSchema.array()),
  getProject: (id) => getJson(`${API_PREFIX}/projects/${id}`, projectSchema, { nullOn: [404] }),
  getGeometry: (id, options) => {
    const query = new URLSearchParams();
    if (options?.simplify) query.set("simplify", String(options.simplify));
    if (options?.maxParts) query.set("max_parts", String(options.maxParts));
    const suffix = query.size ? `?${query}` : "";
    return getJson(`${API_PREFIX}/projects/${id}/geometry${suffix}`, geometrySchema, {
      nullOn: [404],
    });
  },
  getSeries: (id) => getJson(`${API_PREFIX}/projects/${id}/series`, seriesSchema, { nullOn: [404] }),
  getDeclarations: async (id) =>
    (await getJson(`${API_PREFIX}/projects/${id}/declarations`, declarationSchema.array(), {
      nullOn: [404],
    })) ?? [],
  getLatestAudit: (id) =>
    getJson(`${API_PREFIX}/projects/${id}/audit`, auditRunSchema, { nullOn: [404] }),
  chat: (message, sessionRef) =>
    requireJson(`${API_PREFIX}/chat`, chatAnswerSchema, {
      admin: true,
      method: "POST",
      body: { message, session_ref: sessionRef },
      timeoutMs: 90_000,
    }),
  traces: (limit = 50) =>
    requireJson(`${API_PREFIX}/traces?limit=${limit}`, traceSchema.array(), { admin: true }),
  async getReport(runId, format): Promise<ReportFile | null> {
    const response = await send(`${API_PREFIX}/audits/${runId}/report?format=${format}`, {
      nullOn: [404],
      timeoutMs: 60_000,
    });
    if (response === null) return null;
    return {
      body: await response.arrayBuffer(),
      contentType: response.headers.get("content-type") ?? "application/octet-stream",
    };
  },
};
