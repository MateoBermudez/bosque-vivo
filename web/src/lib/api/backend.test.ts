import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BackendError, liveApi } from "./backend";

const project = {
  id: 1,
  source_registry: "Verra",
  registry_id: "VCS-1",
  name: "Proyecto",
  country: "Colombia",
  project_type: null,
  start_year: 2018,
  area_ha: 100.5,
};

const fetchMock = vi.fn<typeof fetch>();

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubEnv("BACKEND_URL", "http://backend.test/");
  vi.stubEnv("ADMIN_TOKEN", "token-secreto");
  vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("cliente del backend", () => {
  it("lee proyectos desde la ruta versionada y valida la forma", async () => {
    fetchMock.mockResolvedValue(json([project]));
    expect(await liveApi.listProjects()).toEqual([project]);
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(String(url)).toBe("http://backend.test/api/v1/projects?limit=200");
    expect((init!.headers as Record<string, string>)["X-Admin-Token"]).toBeUndefined();
  });

  it("pide el polígono liviano solo cuando se le indica", async () => {
    const feature = { type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] } };
    fetchMock.mockImplementation(async () => json(feature));
    await liveApi.getGeometry(3);
    await liveApi.getGeometry(3, { simplify: 0.002, maxParts: 200 });
    expect(String(fetchMock.mock.calls[0]![0])).toBe("http://backend.test/api/v1/projects/3/geometry");
    expect(String(fetchMock.mock.calls[1]![0])).toBe(
      "http://backend.test/api/v1/projects/3/geometry?simplify=0.002&max_parts=200",
    );
  });

  it("devuelve null cuando el backend responde 404", async () => {
    fetchMock.mockResolvedValue(json({ detail: "proyecto no encontrado" }, 404));
    expect(await liveApi.getProject(99)).toBeNull();
    expect(await liveApi.getLatestAudit(99)).toBeNull();
  });

  it("traduce un error del backend usando su mensaje", async () => {
    fetchMock.mockResolvedValue(json({ detail: "servicio de IA no configurado" }, 503));
    await expect(liveApi.chat("hola", "s1")).rejects.toMatchObject({
      name: "BackendError",
      status: 503,
      message: "servicio de IA no configurado",
    });
  });

  it("falla con un mensaje claro si la respuesta no cumple el esquema", async () => {
    fetchMock.mockResolvedValue(json([{ id: "no-es-un-numero" }]));
    await expect(liveApi.listProjects()).rejects.toThrow(/formato esperado/);
  });

  it("avisa cuando no puede conectar con el backend", async () => {
    fetchMock.mockRejectedValue(new TypeError("fetch failed"));
    const error = await liveApi.listProjects().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(BackendError);
    expect((error as BackendError).message).toMatch(/API esté encendida/);
  });

  it("envía el token de administración solo en el chat y las trazas", async () => {
    fetchMock.mockResolvedValueOnce(
      json({ answer: "ok", evidence_ids: [], tools_called: [], used_fallback: false, query_class: "rapida", run_id: 1 }),
    );
    await liveApi.chat("hola", "s1");
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(String(url)).toBe("http://backend.test/api/v1/chat");
    expect(init!.method).toBe("POST");
    expect((init!.headers as Record<string, string>)["X-Admin-Token"]).toBe("token-secreto");
    expect(JSON.parse(String(init!.body))).toEqual({ message: "hola", session_ref: "s1" });
  });

  it("no hace la llamada si falta el token de administración", async () => {
    vi.stubEnv("ADMIN_TOKEN", "");
    await expect(liveApi.traces()).rejects.toThrow(/ADMIN_TOKEN/);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("devuelve el reporte con su tipo de contenido, o null si no existe", async () => {
    fetchMock.mockResolvedValueOnce(new Response("<html></html>", { headers: { "Content-Type": "text/html" } }));
    const file = await liveApi.getReport(7, "html");
    expect(file?.contentType).toBe("text/html");
    expect(String(fetchMock.mock.calls[0]![0])).toBe("http://backend.test/api/v1/audits/7/report?format=html");

    fetchMock.mockResolvedValueOnce(json({ detail: "reporte no generado" }, 404));
    expect(await liveApi.getReport(8, "pdf")).toBeNull();
  });
});
