import type { Series } from "../api";
import { formatInt, formatPct, formatPeople, formatSigned } from "../format";

function Figure({
  label,
  value,
  unit,
  note,
  lead = false,
}: {
  label: string;
  value: string;
  unit?: string;
  note: string;
  lead?: boolean;
}) {
  return (
    <div className="flex flex-col justify-center px-card-pad py-4">
      <div className="type-label text-muted">{label}</div>
      <div className={`num mt-1 ${lead ? "type-figure-lead" : "type-figure"}`}>
        {value}
        {unit && <span className="ml-1 type-body text-muted">{unit}</span>}
      </div>
      <div className="mt-0.5 type-small text-muted">{note}</div>
    </div>
  );
}

export function SummarySkeleton() {
  return (
    <div className="flex h-full flex-col divide-y divide-border">
      {[32, 22, 22].map((h, i) => (
        <div key={i} className="px-card-pad py-4">
          <span className="placeholder block h-3 w-24" />
          <span className="placeholder mt-2 block w-32" style={{ height: h }} />
        </div>
      ))}
    </div>
  );
}

export default function Summary({ data }: { data: Series }) {
  const s = data.summary;
  const change = s.end_population - s.start_population;
  const latest = data.rows[data.rows.length - 1];
  return (
    <div className="flex h-full flex-col divide-y divide-border">
      <Figure
        lead
        label={`Population in ${s.end_year}`}
        value={formatPeople(s.end_population)}
        note={`${formatInt(s.end_population)} people`}
      />
      <div className="grid flex-1 grid-cols-2 divide-x divide-border">
        <Figure
          label={`Change since ${s.start_year}`}
          value={formatSigned(formatPeople(change), change)}
          note={formatPct(s.total_change_pct, 0)}
        />
        <Figure label="Annual growth" value={formatPct(s.cagr * 100, 2, false)} note="compound rate" />
      </div>
      <div className="grid flex-1 grid-cols-2 divide-x divide-border">
        <Figure
          label="Doubling time"
          value={s.doubling_years == null ? "—" : String(Math.round(s.doubling_years))}
          unit={s.doubling_years == null ? undefined : "years"}
          note={s.doubling_years == null ? "not growing" : "at that rate"}
        />
        <Figure
          label="Density"
          value={formatInt(latest.density_per_km2)}
          unit="/km²"
          note={`over ${formatInt(data.area_km2)} km²`}
        />
      </div>
    </div>
  );
}
