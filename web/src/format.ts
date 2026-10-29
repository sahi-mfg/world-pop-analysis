import type { BBox, Row } from "./api";

const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
const full = new Intl.NumberFormat("en", { maximumFractionDigits: 0 });

export const formatCompact = (n: number) => compact.format(n);
export const formatInt = (n: number) => full.format(n);

export function formatPct(n: number | null | undefined, digits = 1, signed = true) {
  if (n == null || !Number.isFinite(n)) return "—";
  const s = n.toFixed(digits);
  return `${signed && n > 0 ? "+" : ""}${s}%`;
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
