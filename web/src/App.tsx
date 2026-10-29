import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { SquareDashedMousePointer } from "lucide-react";
import { Select } from "radix-ui";
import { useEffect, useState } from "react";
import { type BBox, fetchRegions, fetchSeries } from "./api";
import { PeriodControl, SelectContent, SelectItem, StepControl } from "./components/Controls";
import { ChartSkeleton, GrowthChart, PopulationChart } from "./components/Charts";
import DataTable from "./components/DataTable";
import MapView from "./components/MapView";
import Mark from "./components/Mark";
import Panel, { ErrorNotice } from "./components/Panel";
import Sidebar from "./components/Sidebar";
import Summary, { SummarySkeleton } from "./components/Summary";
import { finding, formatPeople, toCsv } from "./format";

const FALLBACK_BBOX: BBox = [-4.15, 5.2, -3.85, 5.45];
const CUSTOM = "custom";

function downloadCsv(text: string, filename: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
  Object.assign(document.createElement("a"), { href: url, download: filename }).click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [selected, setSelected] = useState("abidjan");
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

  const selectRegion = (key: string) => {
    setSelected(key);
    setCustom(null);
    setDrawing(false);
  };

  const name = custom ? "Your area" : (region?.name ?? "");
  const place = custom
    ? `${bbox[1].toFixed(2)}°, ${bbox[0].toFixed(2)}° to ${bbox[3].toFixed(2)}°, ${bbox[2].toFixed(2)}°`
    : (region?.country ?? "");
  const data = series.data;
  const stale = series.isFetching;
  const fileName = `worldpop_${custom ? "custom" : selected}_${years.start}-${years.end}.csv`;

  return (
    <div className="flex min-h-full flex-col lg:h-screen lg:flex-row">
      <Sidebar
        regions={regions.data ?? []}
        loading={regions.isPending}
        selected={custom ? null : selected}
        drawing={drawing}
        customActive={custom != null}
        onSelect={selectRegion}
        onToggleDraw={() => setDrawing((d) => !d)}
      />

      {/* Phone and tablet: the sidebar folds into a bar and one row of area controls. */}
      <header className="flex flex-col gap-3 border-b border-border px-4 py-3 lg:hidden">
        <div className="flex items-center gap-2.5">
          <Mark />
          <span className="type-section">WorldPop Explorer</span>
        </div>
        <div className="flex gap-2">
          <Select.Root value={custom ? CUSTOM : selected} onValueChange={(v) => v !== CUSTOM && selectRegion(v)}>
            <Select.Trigger
              aria-label="Area"
              className="flex h-11 flex-1 items-center justify-between rounded-control border border-control bg-surface px-3 type-body"
            >
              <Select.Value placeholder="Choose an area" />
            </Select.Trigger>
            <SelectContent>
              {(regions.data ?? []).map((r) => (
                <SelectItem key={r.key} value={r.key}>
                  {r.name}, {r.country}
                </SelectItem>
              ))}
              {custom && <SelectItem value={CUSTOM}>Your area</SelectItem>}
            </SelectContent>
          </Select.Root>
          <button
            onClick={() => setDrawing((d) => !d)}
            aria-pressed={drawing}
            className={`flex h-11 items-center gap-2 rounded-control border border-control px-3 type-label ${drawing ? "bg-active" : "bg-surface"}`}
          >
            <SquareDashedMousePointer className="size-4" strokeWidth={1.5} />
            Draw
          </button>
        </div>
      </header>

      <main className="min-w-0 flex-1 px-4 py-5 lg:overflow-y-auto lg:px-canvas-pad lg:py-6">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0">
            <h1 className="type-title">
              {name || <span className="placeholder inline-block h-6 w-40 align-middle" />}
              {place && <span className="ml-2 type-body text-muted">{place}</span>}
            </h1>
            <p className="mt-1 max-w-[72ch] type-body text-muted">
              {data ? (
                finding(name, data.summary, data.rows)
              ) : series.isError ? (
                "No figures for this area yet."
              ) : (
                <span className="placeholder inline-block h-3.5 w-96 max-w-full align-middle" />
              )}
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <PeriodControl start={years.start} end={years.end} onChange={(start, end) => setYears({ start, end })} />
            <StepControl value={step} onChange={setStep} />
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-gap xl:grid-cols-3">
          <section
            aria-label="Map"
            className="relative h-[320px] overflow-hidden rounded-card border border-border bg-surface xl:col-span-2 xl:h-[380px]"
          >
            <MapView
              bbox={bbox}
              regions={regions.data ?? []}
              drawing={drawing}
              callout={data && !stale ? `${formatPeople(data.summary.end_population)} people in ${data.summary.end_year}` : null}
              onDraw={(b) => {
                setCustom(b);
                setDrawing(false);
              }}
              onSelectRegion={selectRegion}
            />
            {(drawing || stale) && (
              <p className="absolute top-3 left-3 rounded-chip bg-surface px-2.5 py-1.5 type-small text-ink shadow-float">
                {drawing ? "Drag a rectangle on the map. Esc cancels." : "Counting people on WorldPop servers…"}
              </p>
            )}
          </section>

          <Panel className="xl:h-[380px]">
            {series.isError ? (
              <div className="p-3">
                <ErrorNotice message={series.error.message} onRetry={() => series.refetch()} />
              </div>
            ) : data ? (
              <div className={`h-full transition-opacity ${stale ? "opacity-50" : ""}`}>
                <Summary data={data} />
              </div>
            ) : (
              <SummarySkeleton />
            )}
          </Panel>

          {data ? (
            <>
              <div className={`xl:col-span-2 ${stale ? "opacity-50" : ""}`}>
                <PopulationChart rows={data.rows} />
              </div>
              <div className={stale ? "opacity-50" : ""}>
                <GrowthChart rows={data.rows} />
              </div>
              <div className={`xl:col-span-3 ${stale ? "opacity-50" : ""}`}>
                <DataTable rows={data.rows} onExport={() => downloadCsv(toCsv(data.rows), fileName)} />
              </div>
            </>
          ) : (
            !series.isError && (
              <>
                <Panel title="Population" subtitle="Residents inside the area, per sample year" className="xl:col-span-2">
                  <ChartSkeleton />
                </Panel>
                <Panel title="Growth per year" subtitle="Annualised between sample years">
                  <ChartSkeleton />
                </Panel>
              </>
            )
          )}
        </div>

        <p className="mt-6 type-small text-muted lg:hidden">
          Data: <a className="underline underline-offset-2" href="https://www.worldpop.org">WorldPop</a>, CC BY 4.0 ·{" "}
          <a className="underline underline-offset-2" href="https://github.com/sahi-mfg/world-pop-analysis">
            Source code
          </a>
        </p>
      </main>
    </div>
  );
}
