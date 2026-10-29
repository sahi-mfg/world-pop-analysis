import type { Summary } from "../api";
import { formatCompact, formatInt, formatPct } from "../format";

function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="panel px-5 py-4">
      <div className="label">{label}</div>
      <div className="mt-2 font-serif text-4xl leading-none tracking-tight">{value}</div>
      {hint && <div className="mt-2 text-xs text-ink-500">{hint}</div>}
    </div>
  );
}

export function KpisSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="skeleton h-[106px] !rounded-2xl" />
      ))}
    </div>
  );
}

export default function Kpis({ s, areaKm2 }: { s: Summary; areaKm2: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Kpi
        label={`Population ${s.end_year}`}
        value={formatCompact(s.end_population)}
        hint={`${formatInt(s.end_population / areaKm2)} people / km²`}
      />
      <Kpi
        label={`Since ${s.start_year}`}
        value={formatPct(s.total_change_pct, 0)}
        hint={`from ${formatCompact(s.start_population)}`}
      />
      <Kpi
        label="Annual growth"
        value={formatPct(s.cagr * 100, 2, false)}
        hint={s.peak_growth_year ? `fastest around ${s.peak_growth_year}` : "compound rate"}
      />
      <Kpi
        label="Doubling time"
        value={s.doubling_years == null ? "—" : `${Math.round(s.doubling_years)} yrs`}
        hint={s.doubling_years == null ? "not growing" : "at the current pace"}
      />
    </div>
  );
}
