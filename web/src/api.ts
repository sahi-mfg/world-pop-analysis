export type BBox = [minLon: number, minLat: number, maxLon: number, maxLat: number];

export interface Region {
  key: string;
  name: string;
  country: string;
  bbox: BBox;
  area_km2: number;
}

export interface Row {
  year: number;
  population: number;
  change: number | null;
  annual_growth_pct: number | null;
  index_100: number;
  density_per_km2: number;
}

export interface Summary {
  start_year: number;
  end_year: number;
  start_population: number;
  end_population: number;
  total_change_pct: number;
  cagr: number;
  doubling_years: number | null;
  peak_growth_year: number | null;
}

export interface Series {
  bbox: BBox;
  area_km2: number;
  rows: Row[];
  summary: Summary;
}

export interface SeriesQuery {
  bbox: BBox;
  start: number;
  end: number;
  step: number;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, { signal });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* non-JSON error page: keep statusText */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export const fetchRegions = (signal?: AbortSignal) => getJson<Region[]>("/api/regions", signal);

export function fetchSeries({ bbox, start, end, step }: SeriesQuery, signal?: AbortSignal) {
  const params = new URLSearchParams({
    bbox: bbox.map((v) => v.toFixed(4)).join(","),
    start: String(start),
    end: String(end),
    step: String(step),
  });
  return getJson<Series>(`/api/series?${params}`, signal);
}
