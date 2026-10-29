import type { Region } from "../api";

interface Props {
  regions: Region[];
  regionsLoading: boolean;
  selected: string | null;
  onSelect: (key: string) => void;
  drawing: boolean;
  onToggleDraw: () => void;
  start: number;
  end: number;
  step: number;
  onYears: (start: number, end: number) => void;
  onStep: (step: number) => void;
}

const YEARS = Array.from({ length: 21 }, (_, i) => 2000 + i);
const STEPS = [1, 2, 5];

function Select({
  value,
  onChange,
  options,
  label,
}: {
  value: number;
  onChange: (v: number) => void;
  options: number[];
  label: string;
}) {
  return (
    <label className="flex-1">
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full appearance-none rounded-lg border border-white/10 bg-ink-800 px-3 py-2 text-sm tabular-nums outline-none transition focus:border-accent"
      >
        {options.map((y) => (
          <option key={y}>{y}</option>
        ))}
      </select>
    </label>
  );
}

export default function Controls(p: Props) {
  return (
    <div className="flex flex-col gap-6">
      <section>
        <h2 className="label mb-3">Featured cities</h2>
        <div className="grid grid-cols-2 gap-2">
          {p.regionsLoading &&
            Array.from({ length: 8 }, (_, i) => <div key={i} className="skeleton h-[58px]" />)}
          {p.regions.map((r) => {
            const active = r.key === p.selected;
            return (
              <button
                key={r.key}
                onClick={() => p.onSelect(r.key)}
                className={`group rounded-xl border px-3 py-2.5 text-left transition ${
                  active
                    ? "border-accent/60 bg-accent-soft"
                    : "border-white/[0.06] bg-ink-800/60 hover:border-white/20 hover:bg-ink-800"
                }`}
              >
                <div className={`text-sm font-medium ${active ? "text-accent" : "text-ink-100"}`}>
                  {r.name}
                </div>
                <div className="truncate text-xs text-ink-500">{r.country}</div>
              </button>
            );
          })}
        </div>
        <button
          onClick={p.onToggleDraw}
          className={`mt-2 flex w-full items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-medium transition ${
            p.drawing
              ? "border-teal/60 bg-teal/10 text-teal"
              : "border-dashed border-white/15 text-ink-300 hover:border-white/30 hover:text-ink-100"
          }`}
        >
          <svg viewBox="0 0 20 20" className="size-4" fill="none" stroke="currentColor" strokeWidth="1.6">
            <rect x="3" y="5" width="14" height="10" rx="1.5" strokeDasharray="2.5 2" />
          </svg>
          {p.drawing ? "Drag on the map… (Esc to cancel)" : "Draw your own area"}
        </button>
      </section>

      <section>
        <h2 className="label mb-3">Period</h2>
        <div className="flex items-center gap-2">
          <Select
            label="Start year"
            value={p.start}
            options={YEARS.filter((y) => y < p.end)}
            onChange={(v) => p.onYears(v, p.end)}
          />
          <span className="text-ink-500">→</span>
          <Select
            label="End year"
            value={p.end}
            options={YEARS.filter((y) => y > p.start)}
            onChange={(v) => p.onYears(p.start, v)}
          />
        </div>
      </section>

      <section>
        <h2 className="label mb-3">Sampling</h2>
        <div className="grid grid-cols-3 gap-1 rounded-xl border border-white/[0.06] bg-ink-800/60 p-1">
          {STEPS.map((s) => (
            <button
              key={s}
              onClick={() => p.onStep(s)}
              className={`rounded-lg py-1.5 text-sm transition ${
                s === p.step ? "bg-ink-700 text-ink-100 shadow" : "text-ink-500 hover:text-ink-300"
              }`}
            >
              every {s} yr
            </button>
          ))}
        </div>
        <p className="mt-2 text-xs leading-relaxed text-ink-500">
          Each sample is a zonal-statistics job on WorldPop servers. Yearly sampling is slower.
        </p>
      </section>
    </div>
  );
}
