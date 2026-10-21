import { describe, expect, it } from "vitest";

import { createSessionToken, verifySessionToken } from "./session";

const SECRET = "un-secreto-de-prueba-bastante-largo";

describe("sesión de auditor", () => {
  it("acepta un token recién creado", async () => {
    const token = await createSessionToken(SECRET);
    expect(await verifySessionToken(token, SECRET)).toBe(true);
  });

  it("rechaza un token firmado con otro secreto", async () => {
    const token = await createSessionToken("otro-secreto");
    expect(await verifySessionToken(token, SECRET)).toBe(false);
  });

  it("rechaza un token vencido", async () => {
    const now = Date.now();
    const token = await createSessionToken(SECRET, now, 60);
    expect(await verifySessionToken(token, SECRET, now + 30_000)).toBe(true);
    expect(await verifySessionToken(token, SECRET, now + 61_000)).toBe(false);
  });

  it("rechaza un token cuyo vencimiento fue alterado", async () => {
    const now = Date.now();
    const token = await createSessionToken(SECRET, now, 60);
    const [version, , signature] = token.split(".");
    const forged = `${version}.${Math.floor(now / 1000) + 999_999}.${signature}`;
    expect(await verifySessionToken(forged, SECRET, now)).toBe(false);
  });

  it.each(["", "abc", "v1.123", "v1.abc.deadbeef", "v2.9999999999.deadbeef", "v1.9999999999.zz", "v1.9999999999."])(
    "rechaza el token mal formado %j",
    async (token) => {
      expect(await verifySessionToken(token, SECRET)).toBe(false);
    },
  );
});
