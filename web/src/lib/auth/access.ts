import { SESSION_COOKIE, readSessionToken, type AuditorSession } from "./session";

export type AuditorAccessMode = "protected" | "open" | "disabled";
export type AuditorLoginMethod = "cuentas" | "codigo";

export function auditorLoginMethod(): AuditorLoginMethod {
  return process.env.BV_DATA_SOURCE === "live" ? "cuentas" : "codigo";
}

export function auditorAccessMode(): AuditorAccessMode {
  const secret = Boolean(process.env.SESSION_SECRET);
  const credentials = auditorLoginMethod() === "cuentas" || Boolean(process.env.AUDITOR_ACCESS_CODE);
  if (secret && credentials) return "protected";
  return process.env.NODE_ENV === "production" ? "disabled" : "open";
}

export async function auditorSession(cookieValue: string | undefined): Promise<AuditorSession | null> {
  if (auditorAccessMode() !== "protected" || !cookieValue) return null;
  return readSessionToken(cookieValue, process.env.SESSION_SECRET!);
}

export async function hasAuditorAccess(cookieValue: string | undefined): Promise<boolean> {
  const mode = auditorAccessMode();
  if (mode === "open") return true;
  if (mode === "disabled") return false;
  return (await auditorSession(cookieValue)) !== null;
}

export { SESSION_COOKIE };

export function safeNextPath(value: string | null | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return "/chat";
  return value;
}
