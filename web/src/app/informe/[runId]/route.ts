import type { NextRequest } from "next/server";

import { attempt, getApi } from "@/lib/api";

// El reporte lo genera el backend. Se entrega desde este origen sin exponer la URL del backend,
// y con una política que impide ejecutar scripts aunque el HTML trajera alguno.
const REPORT_HEADERS = {
  "Content-Security-Policy": "sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src data:",
  "X-Content-Type-Options": "nosniff",
  "Cache-Control": "private, no-store",
} as const;

function messagePage(status: number, title: string, text: string): Response {
  const html = `<!doctype html><html lang="es-CO"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title>
<body style="font-family:system-ui;max-width:32rem;margin:4rem auto;padding:0 1.25rem;line-height:1.5">
<h1 style="font-size:1.4rem">${title}</h1><p>${text}</p><p><a href="/proyectos">Volver a los proyectos</a></p></body></html>`;
  return new Response(html, {
    status,
    headers: { ...REPORT_HEADERS, "Content-Type": "text/html; charset=utf-8" },
  });
}

export async function GET(request: NextRequest, context: RouteContext<"/informe/[runId]">) {
  const { runId: rawId } = await context.params;
  const runId = Number(rawId);
  if (!Number.isInteger(runId) || runId < 1) {
    return messagePage(400, "Reporte no válido", "El identificador del reporte no es correcto.");
  }
  const format = request.nextUrl.searchParams.get("formato") === "pdf" ? "pdf" : "html";

  const result = await attempt(() => getApi().getReport(runId, format));
  if (!result.ok) {
    return messagePage(502, "No pudimos obtener el reporte", result.message);
  }
  if (result.data === null) {
    return messagePage(
      404,
      "El reporte todavía no está disponible",
      "Aún no se ha generado este reporte. Pídele a una persona del equipo auditor que lo genere.",
    );
  }

  return new Response(result.data.body, {
    headers: {
      ...REPORT_HEADERS,
      "Content-Type": result.data.contentType,
      "Content-Disposition": `inline; filename="reporte-${runId}.${format}"`,
    },
  });
}
