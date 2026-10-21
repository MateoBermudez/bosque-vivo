import { SESSION_COOKIE, verifySessionToken } from "./session";

/**
 * - `protected`: hay AUDITOR_ACCESS_CODE y SESSION_SECRET; se exige iniciar sesión.
 * - `open`: sin configurar y en desarrollo; el área de auditores queda abierta para trabajar.
 * - `disabled`: sin configurar y en producción; el área de auditores se bloquea por seguridad.
 */
export type AuditorAccessMode = "protected" | "open" | "disabled";

export function auditorAccessMode(): AuditorAccessMode {
  if (process.env.AUDITOR_ACCESS_CODE && process.env.SESSION_SECRET) return "protected";
  return process.env.NODE_ENV === "production" ? "disabled" : "open";
}

/** Verifica la cookie de sesión de una solicitud (proxy o ruta). */
export async function hasAuditorAccess(cookieValue: string | undefined): Promise<boolean> {
  const mode = auditorAccessMode();
  if (mode === "open") return true;
  if (mode === "disabled") return false;
  if (!cookieValue) return false;
  return verifySessionToken(cookieValue, process.env.SESSION_SECRET!);
}

export { SESSION_COOKIE };

/** Solo se aceptan rutas internas para evitar redirecciones abiertas. */
export function safeNextPath(value: string | null | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return "/chat";
  return value;
}
