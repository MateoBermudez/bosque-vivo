import type { ComparisonRow } from "@/lib/api/schema";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export function ComparisonTable({ rows }: { rows: ComparisonRow[] }) {
  return (
    <div className="card-soft p-6">
      <h2 className="text-xl font-bold">Lo declarado frente a lo observado</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Declarado: desde T0 el proyecto está acreditado y se espera que el bosque permanezca. Observado: verdor
        (NDVI) y hectáreas perdidas cada año.
      </p>
      {rows.length === 0 ? (
        <p className="mt-6 text-sm text-muted-foreground">Todavía no hay datos para comparar.</p>
      ) : (
        <div className="mt-4 max-h-[22rem] overflow-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Comparación anual entre lo declarado y lo observado</caption>
            <thead className="sticky top-0 bg-card text-muted-foreground">
              <tr>
                <th scope="col" className="py-2 pr-3 font-medium">Año</th>
                <th scope="col" className="pr-3 font-medium">Declarado</th>
                <th scope="col" className="pr-3 text-right font-medium">NDVI medio</th>
                <th scope="col" className="text-right font-medium">Pérdida (ha)</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.year} className="border-t border-border">
                  <th scope="row" className="py-2.5 pr-3 font-medium">{row.year}</th>
                  <td className="pr-3">
                    <span
                      className={cn(
                        "rounded-full px-2.5 py-1 text-xs font-semibold",
                        row.after_t0 ? "bg-lime text-lime-foreground" : "bg-secondary text-secondary-foreground",
                      )}
                    >
                      {row.declared_note}
                    </span>
                  </td>
                  <td className="pr-3 text-right tabular-nums">{row.ndvi_mean === null ? "—" : formatNumber(row.ndvi_mean)}</td>
                  <td className="text-right tabular-nums">{formatNumber(row.loss_ha)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
