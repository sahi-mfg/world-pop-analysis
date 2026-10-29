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
import { formatCompact, formatInt, formatPct } from "../format";

const axis = { stroke: "#5b636f", fontSize: 11, tickLine: false, axisLine: false } as const;

function TooltipBox({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-ink-800/95 px-3 py-2 text-xs shadow-xl backdrop-blur">
      <div className="text-ink-500">{title}</div>
      <div className="mt-0.5 text-sm font-medium tabular-nums text-ink-100">{value}</div>
    </div>
  );
}

function ChartPanel({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="panel p-5">
      <div className="mb-4">
        <h3 className="text-sm font-medium">{title}</h3>
        <p className="text-xs text-ink-500">{subtitle}</p>
      </div>
      <div className="h-56">{children}</div>
    </div>
  );
}

export default function Charts({ rows }: { rows: Row[] }) {
  const growth = rows.filter((r) => r.annual_growth_pct != null);
  return (
    <div className="grid gap-3 lg:grid-cols-5">
      <div className="lg:col-span-3">
        <ChartPanel title="Population" subtitle="Estimated residents inside the selected area">
          <ResponsiveContainer>
            <AreaChart data={rows} margin={{ left: -8, right: 8, top: 4 }}>
              <defs>
                <linearGradient id="pop" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f5a524" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#f5a524" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#ffffff0d" vertical={false} />
              <XAxis dataKey="year" {...axis} />
              <YAxis {...axis} tickFormatter={formatCompact} width={52} />
              <Tooltip
                cursor={{ stroke: "#ffffff22" }}
                content={({ active, payload }) =>
                  active && payload?.length ? (
                    <TooltipBox
                      title={String(payload[0].payload.year)}
                      value={`${formatInt(payload[0].payload.population)} people`}
                    />
                  ) : null
                }
              />
              <Area
                type="monotone"
                dataKey="population"
                stroke="#f5a524"
                strokeWidth={2}
                fill="url(#pop)"
                dot={{ r: 3, fill: "#f5a524", strokeWidth: 0 }}
                activeDot={{ r: 5 }}
                animationDuration={900}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>
      <div className="lg:col-span-2">
        <ChartPanel title="Growth rate" subtitle="Annualised, between consecutive samples">
          <ResponsiveContainer>
            <BarChart data={growth} margin={{ left: -16, right: 8, top: 4 }}>
              <CartesianGrid stroke="#ffffff0d" vertical={false} />
              <XAxis dataKey="year" {...axis} />
              <YAxis {...axis} tickFormatter={(v: number) => `${v}%`} width={48} />
              <Tooltip
                cursor={{ fill: "#ffffff08" }}
                content={({ active, payload }) =>
                  active && payload?.length ? (
                    <TooltipBox
                      title={`up to ${payload[0].payload.year}`}
                      value={`${formatPct(payload[0].payload.annual_growth_pct, 2)} / year`}
                    />
                  ) : null
                }
              />
              <Bar dataKey="annual_growth_pct" radius={[6, 6, 0, 0]} animationDuration={900}>
                {growth.map((r) => (
                  <Cell key={r.year} fill={(r.annual_growth_pct ?? 0) >= 0 ? "#2dd4bf" : "#f87171"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>
    </div>
  );
}
