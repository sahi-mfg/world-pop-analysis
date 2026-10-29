import { Check, ChevronDown } from "lucide-react";
import { Select, ToggleGroup } from "radix-ui";

const YEARS = Array.from({ length: 21 }, (_, i) => 2000 + i);
const STEPS = [1, 2, 5];

export function YearSelect({
  label,
  value,
  options = YEARS,
  onChange,
}: {
  label: string;
  value: number;
  options?: number[];
  onChange: (v: number) => void;
}) {
  return (
    <Select.Root value={String(value)} onValueChange={(v) => onChange(Number(v))}>
      <Select.Trigger
        aria-label={label}
        className="num inline-flex h-control-height items-center gap-1.5 rounded-control border border-control bg-surface pr-2 pl-3 type-body hover:bg-raised"
      >
        <Select.Value />
        <Select.Icon>
          <ChevronDown className="size-3.5 text-muted" strokeWidth={1.75} />
        </Select.Icon>
      </Select.Trigger>
      <SelectContent>
        {options.map((y) => (
          <SelectItem key={y} value={String(y)}>
            {y}
          </SelectItem>
        ))}
      </SelectContent>
    </Select.Root>
  );
}

export function SelectContent({ children }: { children: React.ReactNode }) {
  return (
    <Select.Portal>
      <Select.Content
        position="popper"
        sideOffset={4}
        className="z-50 max-h-72 min-w-(--radix-select-trigger-width) overflow-hidden rounded-control border border-border bg-surface shadow-float"
      >
        <Select.Viewport className="p-1">{children}</Select.Viewport>
      </Select.Content>
    </Select.Portal>
  );
}

export function SelectItem({ value, children }: { value: string; children: React.ReactNode }) {
  return (
    <Select.Item
      value={value}
      className="num relative flex h-8 cursor-default items-center rounded-chip pr-8 pl-2.5 type-body outline-none select-none data-highlighted:bg-raised"
    >
      <Select.ItemText>{children}</Select.ItemText>
      <Select.ItemIndicator className="absolute right-2">
        <Check className="size-3.5" strokeWidth={2} />
      </Select.ItemIndicator>
    </Select.Item>
  );
}

export function PeriodControl({
  start,
  end,
  onChange,
}: {
  start: number;
  end: number;
  onChange: (start: number, end: number) => void;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <YearSelect
        label="First year"
        value={start}
        options={YEARS.filter((y) => y < end)}
        onChange={(v) => onChange(v, end)}
      />
      <span className="text-muted">to</span>
      <YearSelect
        label="Last year"
        value={end}
        options={YEARS.filter((y) => y > start)}
        onChange={(v) => onChange(start, v)}
      />
    </div>
  );
}

export function StepControl({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <ToggleGroup.Root
      type="single"
      value={String(value)}
      onValueChange={(v) => v && onChange(Number(v))}
      aria-label="Sample every"
      className="inline-flex h-control-height items-center rounded-control bg-raised p-0.5"
    >
      {STEPS.map((s) => (
        <ToggleGroup.Item
          key={s}
          value={String(s)}
          className="h-full rounded-[4px] px-2.5 type-label text-muted transition-colors hover:text-ink data-[state=on]:bg-surface data-[state=on]:text-ink data-[state=on]:shadow-[0_0_0_1px_var(--color-border)]"
        >
          {s === 1 ? "Yearly" : `${s} yr`}
        </ToggleGroup.Item>
      ))}
    </ToggleGroup.Root>
  );
}
