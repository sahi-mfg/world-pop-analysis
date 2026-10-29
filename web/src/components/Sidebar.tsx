import { SquareDashedMousePointer } from "lucide-react";
import type { Region } from "../api";
import Mark from "./Mark";

interface Props {
  regions: Region[];
  loading: boolean;
  selected: string | null;
  drawing: boolean;
  customActive: boolean;
  onSelect: (key: string) => void;
  onToggleDraw: () => void;
}

const row = "flex h-row-height w-full items-center justify-between gap-3 rounded-control px-3 text-left transition-colors";

export default function Sidebar(p: Props) {
  return (
    <aside className="hidden w-sidebar shrink-0 flex-col border-r border-border lg:flex">
      <div className="flex items-center gap-2.5 px-5 pt-6 pb-5">
        <Mark />
        <span className="type-section">WorldPop Explorer</span>
      </div>

      <nav aria-label="Areas" className="flex-1 overflow-y-auto px-2">
        <h2 className="px-3 pb-2 type-small text-muted">Areas</h2>
        <ul className="flex flex-col gap-0.5">
          {p.loading &&
            Array.from({ length: 8 }, (_, i) => (
              <li key={i} className="flex h-row-height items-center px-3">
                <span className="placeholder h-3.5 w-28" />
              </li>
            ))}
          {p.regions.map((r) => {
            const active = r.key === p.selected;
            return (
              <li key={r.key}>
                <button
                  onClick={() => p.onSelect(r.key)}
                  aria-current={active ? "true" : undefined}
                  className={`${row} ${active ? "bg-active" : "hover:bg-raised"}`}
                >
                  <span className="truncate">{r.name}</span>
                  <span className="shrink-0 type-small text-muted">{r.country}</span>
                </button>
              </li>
            );
          })}
          <li className="mt-1">
            <button
              onClick={p.onToggleDraw}
              aria-pressed={p.drawing}
              className={`${row} ${p.drawing || p.customActive ? "bg-active" : "hover:bg-raised"}`}
            >
              <span className="flex items-center gap-2.5">
                <SquareDashedMousePointer className="size-4 text-muted" strokeWidth={1.5} />
                {p.drawing ? "Drag on the map…" : p.customActive ? "Your area" : "Draw an area"}
              </span>
              {p.drawing && <kbd className="type-small text-muted">Esc</kbd>}
            </button>
          </li>
        </ul>
      </nav>

      <footer className="px-5 py-5 type-small text-muted">
        <p>
          Data:{" "}
          <a className="underline underline-offset-2 hover:text-ink" href="https://www.worldpop.org">
            WorldPop
          </a>
          , CC BY 4.0
        </p>
        <p className="mt-1">
          <a
            className="underline underline-offset-2 hover:text-ink"
            href="https://github.com/sahi-mfg/world-pop-analysis"
          >
            Source code
          </a>
        </p>
      </footer>
    </aside>
  );
}
