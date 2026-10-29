import { Download } from "lucide-react";
import type { Row } from "../api";
import { formatInt, formatPct, formatSigned } from "../format";
import Panel from "./Panel";

const HEAD = ["Year", "Population", "Change", "Growth per year", "People per km²", "Index (first year = 100)"];

export default function DataTable({ rows, onExport }: { rows: Row[]; onExport: () => void }) {
  return (
    <Panel
      title="All samples"
      subtitle={`${rows.length} sample years`}
      action={
        <button
          onClick={onExport}
          className="inline-flex h-control-height shrink-0 items-center gap-1.5 rounded-control border border-control bg-surface px-3 type-label hover:bg-raised"
        >
          <Download className="size-3.5" strokeWidth={1.75} />
          Export CSV
        </button>
      }
    >
      <div className="mt-2 overflow-x-auto">
        <table className="num w-full min-w-[640px] type-body">
          <thead>
            <tr>
              {HEAD.map((h, i) => (
                <th
                  key={h}
                  scope="col"
                  className={`h-9 px-card-pad type-small font-normal text-faint ${i ? "text-right" : "sticky left-0 bg-surface text-left"}`}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.year} className="border-t border-rule">
                <th scope="row" className="sticky left-0 h-row-height bg-surface px-card-pad text-left font-normal">
                  {r.year}
                </th>
                <td className="px-card-pad text-right">{formatInt(r.population)}</td>
                <td className="px-card-pad text-right text-muted">
                  {r.change == null ? "—" : formatSigned(formatInt(r.change), r.change)}
                </td>
                <td className="px-card-pad text-right text-muted">{formatPct(r.annual_growth_pct, 2)}</td>
                <td className="px-card-pad text-right text-muted">{formatInt(r.density_per_km2)}</td>
                <td className="px-card-pad text-right text-muted">{r.index_100.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
