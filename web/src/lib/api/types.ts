import type {
  AuditRun,
  ChatAnswer,
  Declaration,
  Project,
  ProjectGeometry,
  Series,
  Trace,
} from "./schema";

/**
 * Contrato único de acceso a datos. Lo implementan el cliente real (`live`) y los datos
 * de ejemplo (`mock`), de modo que las páginas no saben de dónde vienen los datos.
 */
export interface BosqueVivoApi {
  listProjects(): Promise<Project[]>;
  getProject(id: number): Promise<Project | null>;
  /** `simplify` (grados) aligera el polígono; `maxParts` deja solo las N partes más grandes. */
  getGeometry(
    id: number,
    options?: { simplify?: number; maxParts?: number },
  ): Promise<ProjectGeometry | null>;
  getSeries(id: number): Promise<Series | null>;
  /** Datos del registro del proyecto (metodología, desarrollador, periodo de acreditación…). */
  getDeclarations(id: number): Promise<Declaration[]>;
  /** `null` cuando el proyecto todavía no tiene una auditoría calculada. */
  getLatestAudit(id: number): Promise<AuditRun | null>;
  /** Requiere token de administración en el servidor del backend. */
  chat(message: string, sessionRef: string): Promise<ChatAnswer>;
  /** Requiere token de administración en el servidor del backend. */
  traces(limit?: number): Promise<Trace[]>;
  /** Devuelve el reporte de una corrida, o `null` si todavía no se generó. */
  getReport(runId: number, format: "html" | "pdf"): Promise<ReportFile | null>;
}

export interface ReportFile {
  body: ArrayBuffer | string;
  contentType: string;
}
