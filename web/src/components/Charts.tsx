import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Row } from "../api";
import { formatInt, formatPct, formatPeople, niceTicks, peakGrowth } from "../format";
import Panel from "./Panel";

// Recharts paints SVG attributes, so it gets the DESIGN.md values through CSS variables.
const C = {
  primary: "var(--color-primary)",
  tint: "var(--color-primary-tint)",
  neutral: "var(--color-data-neutral)",
  grid: "var(--color-grid)",
  muted: "var(--color-muted)",
};

const axis = {
  stroke: C.muted,
  fontSize: 12,
  tickLine: false,
  axisLine: false,
  tick: { fill: C.muted },
} as const;

function Tip({ label, value }: { label: string; value: string }) {
  return (
    <div className="num rounded-chip border border-border bg-surface px-2.5 py-1.5 type-small shadow-float">
      <span className="text-muted">{label}</span> <span className="ml-1 text-ink">{value}</span>
    </div>
  );
}

export function ChartSkeleton() {
  return <div className="placeholder mx-card-pad mt-4 mb-card-pad h-[188px]" />;
}

export function PopulationChart({ rows }: { rows: Row[] }) {
  const ticks = niceTicks(Math.max(...rows.map((r) => r.population)));
  return (
    <Panel title="Population" subtitle="Residents inside the area, per sample year">
      <div className="h-[220px] px-2 pt-2 pb-3">
        <ResponsiveContainer>
          <AreaChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={C.grid} vertical={false} />
            <XAxis dataKey="year" {...axis} padding={{ left: 8, right: 8 }} />
            <YAxis
              {...axis}
              ticks={ticks}
              domain={[0, ticks[ticks.length - 1]]}
              tickFormatter={formatPeople}
              width={56}
            />
            <Tooltip
              cursor={{ stroke: C.muted, strokeWidth: 1 }}
              content={({ active, payload }) =>
                active && payload?.length ? (
                  <Tip label={String(payload[0].payload.year)} value={`${formatInt(payload[0].payload.population)} people`} />
                ) : null
              }
            />
            <Area
              type="linear"
              dataKey="population"
              stroke={C.primary}
              strokeWidth={2}
              fill={C.tint}
              fillOpacity={1}
              dot={false}
              activeDot={{ r: 4, fill: C.primary, strokeWidth: 0 }}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}

export function GrowthChart({ rows }: { rows: Row[] }) {
  const growth = rows.filter((r) => r.annual_growth_pct != null);
  const peak = peakGrowth(rows);
  const max = Math.max(0, ...growth.map((r) => r.annual_growth_pct!));
  const min = Math.min(0, ...growth.map((r) => r.annual_growth_pct!));
  const ticks = niceTicks(max);
  return (
    <Panel
      title="Growth per year"
      subtitle={
        peak ? (
          <>
            Fastest from {peak.from} to {peak.to}, <span className="text-primary">{formatPct(peak.pct, 2, false)}</span>
          </>
        ) : (
          "Needs at least two sample years"
        )
      }
    >
      <div className="h-[220px] px-2 pt-2 pb-3">
        {growth.length === 0 ? (
          <p className="px-3 pt-16 type-small text-muted">Choose a longer period to compare years.</p>
        ) : (
          <ResponsiveContainer>
            <BarChart data={growth} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" {...axis} />
              <YAxis
                {...axis}
                ticks={min < 0 ? undefined : ticks}
                domain={[min < 0 ? "auto" : 0, ticks[ticks.length - 1]]}
                tickFormatter={(v: number) => `${v} %`}
                width={44}
              />
              <Tooltip
                cursor={{ fill: "var(--color-raised)" }}
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const r = payload[0].payload as Row;
                  const i = rows.findIndex((x) => x.year === r.year);
                  return <Tip label={`${rows[i - 1].year} to ${r.year}`} value={`${formatPct(r.annual_growth_pct, 2)} a year`} />;
                }}
              />
              <Bar dataKey="annual_growth_pct" radius={[2, 2, 0, 0]} maxBarSize={36} isAnimationActive={false}>
                {growth.map((r) => (
                  <Cell key={r.year} fill={peak && r.year === peak.to ? C.primary : C.neutral} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </Panel>
  );
}
