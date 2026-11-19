import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SESSION_COOKIE, createSessionToken } from "@/lib/auth/session";

import { proxy } from "./proxy";

const SECRET = "secreto-de-prueba";

function request(path: string, token?: string): NextRequest {
  return new NextRequest(`http://localhost:3000${path}`, {
    headers: token ? { cookie: `${SESSION_COOKIE}=${token}` } : {},
  });
}

beforeEach(() => {
  vi.stubEnv("BV_DATA_SOURCE", "live");
  vi.stubEnv("SESSION_SECRET", SECRET);
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("proxy del área de auditores", () => {
  it("manda a un auditor con sesión del asistente público a su chat", async () => {
    const token = await createSessionToken(SECRET, "auditor@example.com");
    const response = await proxy(request("/asistente", token));
    expect(response.status).toBe(307);
    expect(new URL(response.headers.get("location")!).pathname).toBe("/chat");
  });

  it("deja ver el asistente al público sin sesión", async () => {
    const response = await proxy(request("/asistente"));
    expect(response.status).toBe(200);
    expect(response.headers.get("location")).toBeNull();
  });

  it("no trata como auditor una sesión con firma inválida", async () => {
    const forged = await createSessionToken("otro-secreto", "auditor@example.com");
    const response = await proxy(request("/asistente", forged));
    expect(response.headers.get("location")).toBeNull();
  });

  it("sigue exigiendo iniciar sesión para el chat y las trazas", async () => {
    for (const path of ["/chat", "/trazas"]) {
      const response = await proxy(request(path));
      expect(response.status).toBe(307);
      expect(new URL(response.headers.get("location")!).pathname).toBe("/acceso");
    }
  });

  it("responde 401 a la API del chat sin sesión", async () => {
    const response = await proxy(request("/api/chat"));
    expect(response.status).toBe(401);
  });

  it("deja pasar el chat con una sesión válida", async () => {
    const token = await createSessionToken(SECRET, "auditor@example.com");
    const response = await proxy(request("/chat", token));
    expect(response.status).toBe(200);
    expect(response.headers.get("location")).toBeNull();
  });
});
