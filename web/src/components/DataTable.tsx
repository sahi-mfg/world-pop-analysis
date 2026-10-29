import type { Row } from "../api";
import { formatInt, formatPct, toCsv } from "../format";

export default function DataTable({ rows, filename }: { rows: Row[]; filename: string }) {
  const download = () => {
    const url = URL.createObjectURL(new Blob([toCsv(rows)], { type: "text/csv" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: filename });
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="panel overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4">
        <h3 className="text-sm font-medium">Data</h3>
        <button
          onClick={download}
          className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-ink-300 transition hover:border-white/25 hover:text-ink-100"
        >
          Download CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm tabular-nums">
          <thead>
            <tr className="border-y border-white/[0.06] text-left">
              {["Year", "Population", "Change", "Growth / yr", "Density / km²", "Index"].map((h, i) => (
                <th key={h} className={`label px-5 py-2.5 font-medium ${i ? "text-right" : ""}`}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.year} className="border-b border-white/[0.04] last:border-0 hover:bg-white/[0.02]">
                <td className="px-5 py-2.5 text-ink-300">{r.year}</td>
                <td className="px-5 py-2.5 text-right">{formatInt(r.population)}</td>
                <td className="px-5 py-2.5 text-right text-ink-300">
                  {r.change == null ? "—" : `${r.change > 0 ? "+" : ""}${formatInt(r.change)}`}
                </td>
                <td className="px-5 py-2.5 text-right text-ink-300">{formatPct(r.annual_growth_pct, 2)}</td>
                <td className="px-5 py-2.5 text-right text-ink-300">{formatInt(r.density_per_km2)}</td>
                <td className="px-5 py-2.5 text-right text-ink-500">{r.index_100.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
