import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { communityApi } from "./backend";

const fetchMock = vi.fn<typeof fetch>();
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

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

describe("chat en línea", () => {
  it("envía texto con el token de administración", async () => {
    fetchMock.mockResolvedValue(json({ replies: ["Hola"] }));
    expect(await communityApi.send("a1b2c3d4", "hola")).toEqual({
      replies: ["Hola"],
      suggestions: [],
    });
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(String(url)).toBe("http://backend.test/api/v1/community/messages");
    expect((init!.headers as Record<string, string>)["X-Admin-Token"]).toBe("token-secreto");
    expect(JSON.parse(String(init!.body))).toEqual({ session_ref: "a1b2c3d4", message: "hola", kind: "text" });
  });

  it("envía la ubicación del navegador", async () => {
    fetchMock.mockResolvedValue(json({ replies: ["Está dentro del proyecto"] }));
    await communityApi.send("a1b2c3d4", "", { kind: "location", latitude: 5.05, longitude: -74.95 });
    expect(JSON.parse(String(fetchMock.mock.calls[0]![1]!.body))).toEqual({
      session_ref: "a1b2c3d4",
      message: null,
      kind: "location",
      latitude: 5.05,
      longitude: -74.95,
    });
  });

  it("envía una foto con su leyenda", async () => {
    fetchMock.mockResolvedValue(json({ replies: ["En la foto se ve bosque"] }));
    await communityApi.send("a1b2c3d4", "mi finca", { kind: "image", media_base64: "eA==", mime_type: "image/jpeg" });
    const body = JSON.parse(String(fetchMock.mock.calls[0]![1]!.body));
    expect(body).toMatchObject({ kind: "image", message: "mi finca", media_base64: "eA==", mime_type: "image/jpeg" });
  });

  it("devuelve la ficha del proyecto y las sugerencias del asistente", async () => {
    fetchMock.mockResolvedValue(
      json({
        replies: ["Concosta conserva su bosque."],
        project: { project_id: 4, name: "Concosta REDD+ Project", score: 99.1, category: "Alta" },
        suggestions: [{ label: "¿Hay alertas?", message: "ALERTAS" }, { label: "Elegir otro", action: "elegir_proyecto" }],
      }),
    );
    const reply = await communityApi.send("a1b2c3d4", "como va concosta");
    expect(reply.project?.name).toBe("Concosta REDD+ Project");
    expect(reply.suggestions.map((s) => s.label)).toEqual(["¿Hay alertas?", "Elegir otro"]);
  });

  it("rechaza una respuesta con un formato inesperado", async () => {
    fetchMock.mockResolvedValue(json({ replies: "no es una lista" }));
    await expect(communityApi.send("a1b2c3d4", "hola")).rejects.toThrow(/formato esperado/);
  });
});
