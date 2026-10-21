import type { AuditResult } from "@/lib/api/schema";
import { normalizeConfidence, readComponents, readSensitivity, readSensor } from "@/lib/domain";
import { formatNumber, formatPercent } from "@/lib/format";

export function ScoreCard({ result }: { result: AuditResult }) {
  const components = readComponents(result);
  const sensitivity = readSensitivity(result);
  const sensor = readSensor(result);
  const confidence = normalizeConfidence(result.confidence_label);

  return (
    <section aria-labelledby="titulo-indice" className="rounded-[2rem] bg-forest p-6 text-forest-foreground">
      <h2 id="titulo-indice" className="text-sm font-normal text-forest-muted">
        Índice de credibilidad
      </h2>
      <div className="mt-2 flex items-end gap-3">
        <span className="text-7xl font-extrabold text-lime">
          {result.score === null ? "—" : formatNumber(Math.round(result.score))}
        </span>
        <span className="mb-3 text-forest-muted">/ 100</span>
      </div>
      <div className="mt-1">
        <span className="rounded-full bg-forest-foreground px-3 py-1 text-xs font-bold text-forest">
          {result.category}
        </span>
      </div>
      {sensitivity && (
        <p className="mt-3 text-xs text-forest-muted">
          Si se mueven los pesos ±10 puntos, el puntaje queda entre {formatNumber(sensitivity.min)} y{" "}
          {formatNumber(sensitivity.max)}.
        </p>
      )}

      <div className="glass mt-6 rounded-2xl p-4">
        <p className="text-sm font-semibold">
          Confianza {confidence.toLowerCase()} · {formatPercent(result.confidence)}
        </p>
        <p className="mt-1 text-xs text-forest-muted">
          Indica qué tan seguros estamos del índice según la cantidad y calidad de imágenes. No califica al
          proyecto.
        </p>
      </div>

      <ul className="mt-5 space-y-3">
        {components.map((component) => (
          <li key={component.key}>
            <div className="flex justify-between gap-3 text-sm">
              <span>
                {component.label} <span className="text-forest-muted">· {Math.round(component.weight * 100)} %</span>
              </span>
              <span className="font-semibold">
                {component.score === null ? "Sin datos" : formatNumber(component.score)}
              </span>
            </div>
            <div
              className="mt-1.5 h-2 rounded-full bg-forest-foreground/10"
              role="progressbar"
              aria-label={component.label}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={component.score ?? undefined}
              aria-valuetext={component.score === null ? "Sin datos suficientes" : undefined}
            >
              <div
                className="h-2 rounded-full bg-lime"
                style={{ width: `${Math.max(0, Math.min(100, component.score ?? 0))}%` }}
              />
            </div>
            {component.reason && <p className="mt-1 text-xs text-forest-muted">{component.reason}</p>}
            {component.detail.length > 0 && (
              <dl className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-forest-muted">
                {component.detail.map((item) => (
                  <div key={item.label} className="flex gap-1">
                    <dt>{item.label}:</dt>
                    <dd className="text-forest-foreground/90">{item.value}</dd>
                  </div>
                ))}
              </dl>
            )}
          </li>
        ))}
      </ul>
      {sensor && <p className="mt-4 text-xs text-forest-muted">Sensor usado para el cálculo: {sensor}.</p>}
    </section>
  );
}
