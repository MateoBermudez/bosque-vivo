import { describe, expect, it } from "vitest";

import { formatDateTime, formatLatency, formatPercent, formatPeriod } from "./format";

describe("formatDateTime", () => {
  it("trata las fechas sin zona horaria como UTC (así las envía el backend)", () => {
    // 21:29 UTC = 16:29 en Bogotá (UTC-5, sin horario de verano).
    expect(formatDateTime("2026-10-21T21:29:33.344399")).toBe(formatDateTime("2026-10-21T21:29:33.344399Z"));
    expect(formatDateTime("2026-10-21T21:29:33Z")).toMatch(/4:29/);
  });

  it("respeta una zona horaria explícita", () => {
    expect(formatDateTime("2026-10-21T16:29:00-05:00")).toBe(formatDateTime("2026-10-21T21:29:00Z"));
  });

  it("devuelve el texto original si no es una fecha", () => {
    expect(formatDateTime("no-es-fecha")).toBe("no-es-fecha");
  });
});

describe("otros formatos", () => {
  it("formatea latencias", () => {
    expect(formatLatency(850)).toBe("850 ms");
    expect(formatLatency(6420)).toBe("6.4 s");
    expect(formatLatency(null)).toBe("—");
  });

  it("formatea porcentajes y periodos", () => {
    expect(formatPercent(0.876)).toBe("88 %");
    expect(formatPeriod("2016-03-01")).toMatch(/mar.*2016/);
  });
});
