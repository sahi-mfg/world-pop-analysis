import { describe, expect, it } from "vitest";
import type { Row, Summary } from "./api";
import {
  bboxAreaKm2,
  finding,
  formatPct,
  formatPeople,
  niceTicks,
  normalizeBBox,
  peakGrowth,
  toCsv,
} from "./format";

const row = (year: number, population: number, growth: number | null): Row => ({
  year,
  population,
  change: null,
  annual_growth_pct: growth,
  index_100: 100,
  density_per_km2: 1,
});

const rows = [row(2000, 3e6, null), row(2010, 4.2e6, 3.4), row(2020, 6.45e6, 4.4)];
const summary: Summary = {
  start_year: 2000,
  end_year: 2020,
  start_population: 3e6,
  end_population: 6.45e6,
  total_change_pct: 115,
  cagr: 0.039,
  doubling_years: 18,
  peak_growth_year: 2020,
};

describe("format", () => {
  it("formats percentages with sign and placeholder", () => {
    expect(formatPct(4.236)).toBe("+4.2 %");
    expect(formatPct(-1)).toBe("-1.0 %");
    expect(formatPct(null)).toBe("—");
    expect(formatPct(3, 2, false)).toBe("3.00 %");
  });

  it("formats people at fixed precision per magnitude", () => {
    expect(formatPeople(6_448_107)).toBe("6.45 M");
    expect(formatPeople(923_400)).toBe("923 k");
    expect(formatPeople(812)).toBe("812");
  });

  it("builds round ticks from zero with the top one above the maximum", () => {
    expect(niceTicks(6.45e6)).toEqual([0, 2e6, 4e6, 6e6, 8e6]);
    expect(niceTicks(4.4)).toEqual([0, 2, 4, 6]);
    expect(niceTicks(0)).toEqual([0, 1]);
  });

  it("matches the backend area formula", () => {
    expect(bboxAreaKm2([0, 0, 1, 1])).toBeCloseTo(12_363, -1);
  });

  it("normalizes a dragged rectangle in any direction", () => {
    expect(normalizeBBox([3, 7], [1, 5])).toEqual([1, 5, 3, 7]);
  });

  it("finds the fastest growth period", () => {
    expect(peakGrowth(rows)).toEqual({ from: 2010, to: 2020, pct: 4.4 });
    expect(peakGrowth([row(2020, 1, null)])).toBeNull();
  });

  it("states the finding with its baselines", () => {
    expect(finding("Lagos", summary, rows)).toBe(
      "Lagos grew from 3.00 M to 6.45 M people between 2000 and 2020 (+115 %). " +
        "Growth was fastest from 2010 to 2020, at 4.40 % a year.",
    );
  });

  it("writes CSV with empty cells for nulls", () => {
    expect(toCsv([row(2000, 10, null)]).split("\n")[1]).toBe("2000,10,,,100,1");
  });
});
