const hectares = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
const decimals = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 });

export function formatHa(value: number | null | undefined): string {
  return value == null ? "—" : `${hectares.format(value)} ha`;
}

export function formatNumber(value: number | null | undefined): string {
  return value == null ? "—" : decimals.format(value);
}

export function formatPercent(fraction: number): string {
  return `${Math.round(fraction * 100)} %`;
}

/** El backend envía fechas ISO sin zona horaria (son UTC); se les añade la «Z» para no leerlas como hora local. */
function parseServerDate(iso: string): Date {
  return new Date(/(?:Z|[+-]\d{2}:?\d{2})$/.test(iso) ? iso : `${iso}Z`);
}

/** Fecha y hora en español de Colombia. Acepta ISO 8601 con o sin zona horaria. */
export function formatDateTime(iso: string): string {
  const date = parseServerDate(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Bogota",
  }).format(date);
}

export function formatLatency(ms: number | null | undefined): string {
  if (ms == null) return "—";
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

/** "2016-03-01" -> "mar 2016" (los datos mensuales llegan con día 1). */
export function formatPeriod(period: string): string {
  const date = new Date(`${period}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return period;
  return new Intl.DateTimeFormat("es-CO", { month: "short", year: "numeric", timeZone: "UTC" })
    .format(date)
    .replace(".", "");
}
