import { describe, expect, it } from "vitest";

import { createSessionToken, readSessionToken, verifySessionToken } from "./session";

const SECRET = "un-secreto-de-prueba-bastante-largo";

describe("sesión de auditor", () => {
  it("acepta un token recién creado y conserva el usuario", async () => {
    const token = await createSessionToken(SECRET, "auditora@elpoli.edu.co");
    expect(await verifySessionToken(token, SECRET)).toBe(true);
    expect((await readSessionToken(token, SECRET))?.subject).toBe("auditora@elpoli.edu.co");
  });

  it("rechaza un token firmado con otro secreto", async () => {
    const token = await createSessionToken("otro-secreto");
    expect(await verifySessionToken(token, SECRET)).toBe(false);
  });

  it("rechaza un token vencido", async () => {
    const now = Date.now();
    const token = await createSessionToken(SECRET, "a@b.co", now, 60);
    expect(await verifySessionToken(token, SECRET, now + 30_000)).toBe(true);
    expect(await verifySessionToken(token, SECRET, now + 61_000)).toBe(false);
  });

  it("rechaza un token cuyo vencimiento fue alterado", async () => {
    const now = Date.now();
    const token = await createSessionToken(SECRET, "a@b.co", now, 60);
    const [version, , subject, signature] = token.split(".");
    const forged = `${version}.${Math.floor(now / 1000) + 999_999}.${subject}.${signature}`;
    expect(await verifySessionToken(forged, SECRET, now)).toBe(false);
  });

  it("rechaza un token cuyo usuario fue alterado", async () => {
    const token = await createSessionToken(SECRET, "a@b.co");
    const [version, expires, , signature] = token.split(".");
    const other = Buffer.from("admin@b.co").toString("hex");
    expect(await verifySessionToken(`${version}.${expires}.${other}.${signature}`, SECRET)).toBe(false);
  });

  it.each([
    "",
    "abc",
    "v2.123",
    "v2.abc.61.deadbeef",
    "v1.9999999999.deadbeef",
    "v2.9999999999.61.zz",
    "v2.9999999999.zz.deadbeef",
    "v2.9999999999.61.",
  ])("rechaza el token mal formado %j", async (token) => {
    expect(await verifySessionToken(token, SECRET)).toBe(false);
  });
});
