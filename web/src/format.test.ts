import { describe, expect, it } from "vitest";
import { bboxAreaKm2, formatCompact, formatPct, normalizeBBox, toCsv } from "./format";

describe("format", () => {
  it("formats percentages with sign and placeholder", () => {
    expect(formatPct(4.236)).toBe("+4.2%");
    expect(formatPct(-1)).toBe("-1.0%");
    expect(formatPct(null)).toBe("—");
    expect(formatPct(3, 2, false)).toBe("3.00%");
  });

  it("formats compact numbers", () => {
    expect(formatCompact(15_400_000)).toBe("15.4M");
  });

  it("matches the backend area formula", () => {
    expect(bboxAreaKm2([0, 0, 1, 1])).toBeCloseTo(12_363, -1);
  });

  it("normalizes a dragged rectangle in any direction", () => {
    expect(normalizeBBox([3, 7], [1, 5])).toEqual([1, 5, 3, 7]);
  });

  it("writes CSV with empty cells for nulls", () => {
    const csv = toCsv([
      { year: 2000, population: 10, change: null, annual_growth_pct: null, index_100: 100, density_per_km2: 1 },
    ]);
    expect(csv.split("\n")[1]).toBe("2000,10,,,100,1");
  });
});
