"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatNumber } from "@/lib/format";

export function LossChart({ loss }: { loss: { year: number; ha_lost: number }[] }) {
  if (loss.length === 0) {
    return <p className="py-10 text-center text-sm text-muted-foreground">No hay pérdida de bosque registrada.</p>;
  }
  const total = loss.reduce((sum, item) => sum + item.ha_lost, 0);
  return (
    <div
      role="img"
      aria-label={`Pérdida de bosque por año entre ${loss[0]!.year} y ${loss[loss.length - 1]!.year}: ${formatNumber(total)} hectáreas en total.`}
    >
      <ResponsiveContainer width="100%" height={240} initialDimension={{ width: 560, height: 240 }}>
        <BarChart data={loss} margin={{ left: -10, right: 10, top: 10 }}>
          <CartesianGrid stroke="var(--border)" vertical={false} />
          <XAxis dataKey="year" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
          <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
          <Tooltip
            formatter={(value) => [`${formatNumber(typeof value === "number" ? value : Number(value))} ha`, "Pérdida"]}
            contentStyle={{ borderRadius: 12, border: "1px solid var(--border)" }}
          />
          <Bar dataKey="ha_lost" fill="var(--cat-baja)" radius={[6, 6, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
