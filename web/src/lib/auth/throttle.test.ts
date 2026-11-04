import { describe, expect, it } from "vitest";

import { createThrottle, passwordProblem } from "./throttle";

describe("límite de intentos", () => {
  it("bloquea después del máximo y libera al vencer", () => {
    const throttle = createThrottle(3, 1000);
    const now = 10_000;
    for (let i = 0; i < 3; i++) throttle.fail("ip", now);
    expect(throttle.blocked("ip", now + 10)).toBe(true);
    expect(throttle.blocked("ip", now + 1001)).toBe(false);
    throttle.fail("ip", now + 1002);
    expect(throttle.blocked("ip", now + 1003)).toBe(false);
  });

  it("reinicia la cuenta tras un acierto", () => {
    const throttle = createThrottle(2, 1000);
    throttle.fail("ip", 0);
    throttle.reset("ip");
    throttle.fail("ip", 1);
    expect(throttle.blocked("ip", 2)).toBe(false);
  });
});

describe("validación de contraseña nueva", () => {
  it.each([
    ["Clave2026xx", "Clave2026xy", "no coinciden"],
    ["corta1", "corta1", "al menos 10"],
    ["soloLetrasAqui", "soloLetrasAqui", "letra y un número"],
    ["12345678901", "12345678901", "letra y un número"],
  ])("rechaza %j", (password, confirmation, fragment) => {
    expect(passwordProblem(password, confirmation)).toContain(fragment);
  });

  it("acepta una contraseña válida", () => {
    expect(passwordProblem("BosqueVivo2026", "BosqueVivo2026")).toBeNull();
  });
});
