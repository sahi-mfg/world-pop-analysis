import type { BBox, Row, Summary } from "./api";

const int = new Intl.NumberFormat("en", { maximumFractionDigits: 0 });

export const formatInt = (n: number) => int.format(n);

/** "6.45 M", "923 k", "812": fixed precision per magnitude so figures line up. */
export function formatPeople(n: number) {
  const abs = Math.abs(n);
  if (abs >= 1e6) return `${(n / 1e6).toFixed(2)} M`;
  if (abs >= 1e4) return `${(n / 1e3).toFixed(0)} k`;
  return int.format(n);
}

export function formatSigned(text: string, n: number) {
  return n > 0 ? `+${text}` : text;
}

export function formatPct(n: number | null | undefined, digits = 1, signed = true) {
  if (n == null || !Number.isFinite(n)) return "—";
  const s = `${n.toFixed(digits)} %`;
  return signed && n > 0 ? `+${s}` : s;
}

/** Round axis ticks from zero, the top one above the maximum. */
export function niceTicks(max: number, count = 4): number[] {
  if (max <= 0) return [0, 1];
  const raw = max / count;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s * count >= max * 1.0001)!;
  const ticks = [];
  for (let v = 0; v <= max + step * 0.0001 || ticks.length < 2; v += step) ticks.push(v);
  if (ticks[ticks.length - 1] <= max) ticks.push(ticks[ticks.length - 1] + step);
  return ticks;
}

/** Area of a lon/lat box on a spherical Earth, matching the backend formula. */
export function bboxAreaKm2([minLon, minLat, maxLon, maxLat]: BBox) {
  const R = 6371.0088;
  const rad = Math.PI / 180;
  return R * R * (maxLon - minLon) * rad * (Math.sin(maxLat * rad) - Math.sin(minLat * rad));
}

export function normalizeBBox(a: [number, number], b: [number, number]): BBox {
  return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])];
}

/** The sample with the fastest annualised growth, if the series has more than one sample. */
export function peakGrowth(rows: Row[]): { from: number; to: number; pct: number } | null {
  let best: { from: number; to: number; pct: number } | null = null;
  rows.forEach((r, i) => {
    if (i === 0 || r.annual_growth_pct == null) return;
    if (!best || r.annual_growth_pct > best.pct) {
      best = { from: rows[i - 1].year, to: r.year, pct: r.annual_growth_pct };
    }
  });
  return best;
}

/** The screen's one finding, stated with its baselines. */
export function finding(name: string, s: Summary, rows: Row[]) {
  if (s.start_year === s.end_year) {
    return `${name} had ${formatPeople(s.end_population)} people in ${s.end_year}.`;
  }
  const verb = s.end_population >= s.start_population ? "grew" : "shrank";
  let text =
    `${name} ${verb} from ${formatPeople(s.start_population)} to ` +
    `${formatPeople(s.end_population)} people between ${s.start_year} and ${s.end_year} ` +
    `(${formatPct(s.total_change_pct, 0)}).`;
  const peak = peakGrowth(rows);
  if (peak && rows.length > 2 && peak.pct > 0) {
    text += ` Growth was fastest from ${peak.from} to ${peak.to}, at ${formatPct(peak.pct, 2, false)} a year.`;
  }
  return text;
}

export function toCsv(rows: Row[]) {
  const cols: (keyof Row)[] = [
    "year",
    "population",
    "change",
    "annual_growth_pct",
    "index_100",
    "density_per_km2",
  ];
  const lines = rows.map((r) => cols.map((c) => r[c] ?? "").join(","));
  return [cols.join(","), ...lines].join("\n");
}
