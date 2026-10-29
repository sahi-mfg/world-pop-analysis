import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { type BBox, fetchRegions, fetchSeries } from "./api";
import Charts from "./components/Charts";
import Controls from "./components/Controls";
import DataTable from "./components/DataTable";
import Kpis, { KpisSkeleton } from "./components/Kpis";
import MapView from "./components/MapView";
import { bboxAreaKm2, formatInt } from "./format";

const FALLBACK_BBOX: BBox = [-4.15, 5.2, -3.85, 5.45];

export default function App() {
  const [selected, setSelected] = useState<string | null>("abidjan");
  const [custom, setCustom] = useState<BBox | null>(null);
  const [drawing, setDrawing] = useState(false);
  const [years, setYears] = useState({ start: 2000, end: 2020 });
  const [step, setStep] = useState(5);

  const regions = useQuery({ queryKey: ["regions"], queryFn: ({ signal }) => fetchRegions(signal) });
  const region = regions.data?.find((r) => r.key === selected);
  const bbox = custom ?? region?.bbox ?? FALLBACK_BBOX;

  const series = useQuery({
    queryKey: ["series", bbox, years.start, years.end, step],
    queryFn: ({ signal }) => fetchSeries({ bbox, ...years, step }, signal),
    enabled: regions.isSuccess || custom != null,
    placeholderData: keepPreviousData,
  });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setDrawing(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const title = custom ? "Custom area" : region ? region.name : "Loading…";
  const subtitle = custom ? bbox.map((v) => v.toFixed(2)).join(", ") : region?.country ?? "";
  const area = useMemo(() => bboxAreaKm2(bbox), [bbox]);
  const loading = series.isFetching;

  return (
    <div className="flex min-h-full flex-col lg:h-full lg:flex-row">
      <aside className="flex shrink-0 flex-col gap-8 border-white/[0.06] p-6 lg:w-[360px] lg:overflow-y-auto lg:border-r">
        <header>
          <div className="flex items-center gap-2 text-accent">
            <img src="/favicon.svg" alt="" className="size-5" />
            <span className="text-xs font-semibold uppercase tracking-[0.2em]">WorldPop Explorer</span>
          </div>
          <h1 className="mt-4 font-serif text-[2.6rem] leading-[1.05] tracking-tight">
            How fast are the world&rsquo;s cities <em className="text-accent">growing</em>?
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-ink-300">
            Two decades of 100&nbsp;m population estimates, aggregated on demand for any area on
            Earth.
          </p>
        </header>

        <Controls
          regions={regions.data ?? []}
          regionsLoading={regions.isPending}
          selected={custom ? null : selected}
          onSelect={(k) => {
            setSelected(k);
            setCustom(null);
            setDrawing(false);
          }}
          drawing={drawing}
          onToggleDraw={() => setDrawing((d) => !d)}
          start={years.start}
          end={years.end}
          step={step}
          onYears={(start, end) => setYears({ start, end })}
          onStep={setStep}
        />

        <footer className="mt-auto space-y-1 text-xs leading-relaxed text-ink-500">
          <p>
            Data ©{" "}
            <a className="underline decoration-white/20 hover:text-ink-300" href="https://www.worldpop.org">
              WorldPop
            </a>{" "}
            (CC BY 4.0) · Global 100 m unconstrained counts, 2000–2020.
          </p>
          <p>
            <a
              className="underline decoration-white/20 hover:text-ink-300"
              href="https://github.com/sahi-mfg/world-pop-analysis"
            >
              Source on GitHub
            </a>
          </p>
        </footer>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col gap-3 p-3 lg:overflow-y-auto">
        <section className="panel relative h-[46vh] min-h-[320px] overflow-hidden">
          <MapView
            bbox={bbox}
            regions={regions.data ?? []}
            drawing={drawing}
            onDraw={(b) => {
              setCustom(b);
              setDrawing(false);
            }}
            onSelectRegion={(k) => {
              setSelected(k);
              setCustom(null);
            }}
          />
          <div className="pointer-events-none absolute bottom-4 left-4 rounded-xl border border-white/10 bg-ink-950/75 px-4 py-3 backdrop-blur">
            <div className="font-serif text-2xl leading-none">{title}</div>
            <div className="mt-1 text-xs text-ink-300">
              {subtitle} · {formatInt(area)} km²
            </div>
          </div>
          {loading && (
            <div className="absolute top-4 left-4 flex items-center gap-2 rounded-full border border-white/10 bg-ink-950/75 px-3 py-1.5 text-xs text-ink-300 backdrop-blur">
              <span className="size-2 animate-pulse rounded-full bg-accent" />
              Running zonal statistics…
            </div>
          )}
        </section>

        {series.isError ? (
          <div className="panel flex flex-col items-start gap-3 border-red-400/20 p-6">
            <div className="label !text-red-300">Could not retrieve data</div>
            <p className="max-w-3xl font-mono text-sm break-words text-ink-300">
              {series.error.message}
            </p>
            <button
              onClick={() => series.refetch()}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-sm hover:border-white/25"
            >
              Try again
            </button>
          </div>
        ) : series.data ? (
          <div className={`flex flex-col gap-3 transition-opacity ${loading ? "opacity-50" : ""}`}>
            <Kpis s={series.data.summary} areaKm2={series.data.area_km2} />
            <Charts rows={series.data.rows} />
            <DataTable rows={series.data.rows} filename={`worldpop_${custom ? "custom" : selected}.csv`} />
          </div>
        ) : (
          <>
            <KpisSkeleton />
            <div className="skeleton h-72 !rounded-2xl" />
          </>
        )}
      </main>
    </div>
  );
}
