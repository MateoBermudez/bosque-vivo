import { afterEach, describe, expect, it, vi } from "vitest";

import { auditorAccessMode, auditorLoginMethod, auditorSession, hasAuditorAccess, safeNextPath } from "./access";
import { createSessionToken } from "./session";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("safeNextPath", () => {
  it("acepta rutas internas", () => {
    expect(safeNextPath("/trazas")).toBe("/trazas");
    expect(safeNextPath("/chat?proyecto=3")).toBe("/chat?proyecto=3");
  });

  it.each(["https://malo.example", "//malo.example", "/\\malo.example", "javascript:alert(1)", "", undefined, null])(
    "descarta %j y vuelve al chat",
    (value) => {
      expect(safeNextPath(value)).toBe("/chat");
    },
  );
});

describe("modo de acceso de auditores", () => {
  it("queda protegido cuando hay código y secreto", () => {
    vi.stubEnv("AUDITOR_ACCESS_CODE", "codigo");
    vi.stubEnv("SESSION_SECRET", "secreto");
    expect(auditorAccessMode()).toBe("protected");
  });

  it("usa cuentas de auditor con la API en vivo y basta el secreto", () => {
    vi.stubEnv("BV_DATA_SOURCE", "live");
    vi.stubEnv("AUDITOR_ACCESS_CODE", "");
    vi.stubEnv("SESSION_SECRET", "secreto");
    expect(auditorLoginMethod()).toBe("cuentas");
    expect(auditorAccessMode()).toBe("protected");
  });

  it("usa el código sin API en vivo", () => {
    vi.stubEnv("BV_DATA_SOURCE", "mock");
    vi.stubEnv("AUDITOR_ACCESS_CODE", "");
    vi.stubEnv("SESSION_SECRET", "secreto");
    vi.stubEnv("NODE_ENV", "development");
    expect(auditorLoginMethod()).toBe("codigo");
    expect(auditorAccessMode()).toBe("open");
  });

  it("devuelve el usuario de la sesión", async () => {
    vi.stubEnv("BV_DATA_SOURCE", "live");
    vi.stubEnv("SESSION_SECRET", "secreto");
    const session = await auditorSession(await createSessionToken("secreto", "a@b.co"));
    expect(session?.subject).toBe("a@b.co");
  });

  it("queda abierto en desarrollo sin configuración", () => {
    vi.stubEnv("BV_DATA_SOURCE", "mock");
    vi.stubEnv("AUDITOR_ACCESS_CODE", "");
    vi.stubEnv("SESSION_SECRET", "");
    vi.stubEnv("NODE_ENV", "development");
    expect(auditorAccessMode()).toBe("open");
  });

  it("se bloquea en producción sin configuración", () => {
    vi.stubEnv("AUDITOR_ACCESS_CODE", "");
    vi.stubEnv("SESSION_SECRET", "");
    vi.stubEnv("NODE_ENV", "production");
    expect(auditorAccessMode()).toBe("disabled");
  });

  it("exige una cookie válida cuando está protegido", async () => {
    vi.stubEnv("AUDITOR_ACCESS_CODE", "codigo");
    vi.stubEnv("SESSION_SECRET", "secreto");
    expect(await hasAuditorAccess(undefined)).toBe(false);
    expect(await hasAuditorAccess("basura")).toBe(false);
    expect(await hasAuditorAccess(await createSessionToken("secreto"))).toBe(true);
    expect(await hasAuditorAccess(await createSessionToken("otro"))).toBe(false);
  });

  it("niega siempre el acceso cuando está deshabilitado", async () => {
    vi.stubEnv("AUDITOR_ACCESS_CODE", "");
    vi.stubEnv("SESSION_SECRET", "");
    vi.stubEnv("NODE_ENV", "production");
    expect(await hasAuditorAccess(await createSessionToken("secreto"))).toBe(false);
  });
});
