import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BackendError, accountsApi } from "./backend";

const fetchMock = vi.fn<typeof fetch>();

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubEnv("BACKEND_URL", "http://backend.test");
  vi.stubEnv("ADMIN_TOKEN", "token-secreto");
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("cuentas de auditor (RF09)", () => {
  it("inicia sesión con el token de administración del servidor", async () => {
    fetchMock.mockResolvedValue(json({ email: "a@b.co", name: "Ana" }));
    expect(await accountsApi.login("a@b.co", "BosqueVivo2026")).toEqual({ email: "a@b.co", name: "Ana" });
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(String(url)).toBe("http://backend.test/api/v1/auth/login");
    expect((init!.headers as Record<string, string>)["X-Admin-Token"]).toBe("token-secreto");
    expect(JSON.parse(String(init!.body))).toEqual({ email: "a@b.co", password: "BosqueVivo2026" });
  });

  it("propaga el mensaje y el estado de credenciales inválidas", async () => {
    fetchMock.mockResolvedValue(json({ detail: "El correo o la contraseña no son correctos." }, 401));
    const error = await accountsApi.login("a@b.co", "x").catch((reason: unknown) => reason);
    expect(error).toBeInstanceOf(BackendError);
    expect((error as BackendError).status).toBe(401);
  });

  it("solicita, verifica y confirma el restablecimiento", async () => {
    fetchMock
      .mockResolvedValueOnce(json({ detail: "Si la dirección está registrada…" }, 202))
      .mockResolvedValueOnce(json({ status: "valido", detail: null }))
      .mockResolvedValueOnce(json({ detail: "Tu contraseña se actualizó." }));
    expect(await accountsApi.requestReset("a@b.co")).toContain("Si la dirección");
    expect((await accountsApi.verifyReset("tok")).status).toBe("valido");
    expect(await accountsApi.confirmReset("tok", "NuevaClave2026")).toContain("actualizó");
    expect(fetchMock.mock.calls.map(([url]) => String(url))).toEqual([
      "http://backend.test/api/v1/auth/password-reset",
      "http://backend.test/api/v1/auth/password-reset/verify",
      "http://backend.test/api/v1/auth/password-reset/confirm",
    ]);
  });

  it("informa un enlace vencido con estado 410", async () => {
    fetchMock.mockResolvedValue(json({ detail: "El enlace venció. Solicita uno nuevo." }, 410));
    const error = await accountsApi.confirmReset("tok", "NuevaClave2026").catch((reason: unknown) => reason);
    expect((error as BackendError).status).toBe(410);
    expect((error as BackendError).message).toContain("venció");
  });
});
