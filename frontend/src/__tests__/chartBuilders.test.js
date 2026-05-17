import { describe, it, expect } from "vitest";
import {
  toNumber,
  buildBarOption,
  buildLineOption,
  buildHistogramOption,
  buildMissingRateOption,
  buildNumericOption,
  buildTypeDistributionOption,
  buildFrequencyOption,
  buildParetoOption,
  buildBoxplotOption,
  buildCorrelationOption,
  buildGroupStatsOption,
  buildBinningOption,
  buildViolinOption,
  buildScatterOption,
  buildMissingHeatmapOption,
  buildTimeseriesOption,
  buildOutliersOption,
  buildComparisonHistogramOption,
} from "../composables/chartBuilders";

describe("toNumber", () => {
  it("converts valid numbers", () => {
    expect(toNumber(42)).toBe(42);
    expect(toNumber("3.14")).toBe(3.14);
  });
  it("returns 0 for NaN", () => {
    expect(toNumber(NaN)).toBe(0);
    expect(toNumber(undefined)).toBe(0);
    expect(toNumber(null)).toBe(0);
  });
});

describe("buildBarOption", () => {
  const option = buildBarOption(["a", "b"], [1, 2], "%");
  it("creates bar series", () => {
    expect(option.series[0].type).toBe("bar");
    expect(option.xAxis.data).toEqual(["a", "b"]);
  });
  it("applies unit formatter", () => {
    expect(option.yAxis.axisLabel.formatter).toBe("{value}%");
  });
});

describe("buildLineOption", () => {
  const option = buildLineOption(["a", "b"], [1, 2], "");
  it("creates line series", () => {
    expect(option.series[0].type).toBe("line");
    expect(option.series[0].smooth).toBe(true);
  });
});

describe("buildHistogramOption", () => {
  const report = {
    histograms: {
      age: { bins: [0, 10, 20, 30], counts: [5, 10, 5] },
    },
  };
  it("creates option for valid histogram", () => {
    const opt = buildHistogramOption(report, "age");
    expect(opt).not.toBeNull();
    expect(opt.series).toHaveLength(2);
    expect(opt.xAxis.data).toHaveLength(3);
  });
  it("returns null for missing feature", () => {
    expect(buildHistogramOption(report, "nonexistent")).toBeNull();
  });
  it("returns null for empty histograms", () => {
    expect(buildHistogramOption({ histograms: {} }, "x")).toBeNull();
  });
});

describe("buildMissingRateOption", () => {
  const report = {
    missing_rate: { a: 0.1, b: 0.2, c: 0.0 },
  };
  it("converts rates to percentages", () => {
    const opt = buildMissingRateOption(report, "bar");
    const values = opt.series[0].data;
    expect(values).toEqual([10, 20, 0]);
  });
  it("returns null for empty", () => {
    expect(buildMissingRateOption({ missing_rate: {} }, "bar")).toBeNull();
  });
});

describe("buildNumericOption", () => {
  it("builds bar option from numeric summary", () => {
    const report = {
      numeric_summary: { x: { mean: 5 }, y: { mean: 10 } },
    };
    const opt = buildNumericOption(report, "mean", "bar");
    expect(opt.series[0].data).toEqual([5, 10]);
  });
  it("returns null for empty summary", () => {
    expect(buildNumericOption({ numeric_summary: {} }, "mean", "bar")).toBeNull();
  });
});

describe("buildTypeDistributionOption", () => {
  it("counts dtype occurrences", () => {
    const report = {
      dtypes: { a: "object", b: "int64", c: "object", d: "float64" },
    };
    const opt = buildTypeDistributionOption(report, "bar");
    const cats = opt.xAxis.data;
    expect(cats).toContain("object");
    expect(cats).toContain("int64");
    expect(cats).toContain("float64");
  });
  it("returns null for empty", () => {
    expect(buildTypeDistributionOption({ dtypes: {} }, "bar")).toBeNull();
  });
});

describe("buildFrequencyOption", () => {
  const report = {
    frequencies: { dept: [{ value: "Eng", count: 5 }, { value: "Sales", count: 3 }] },
  };
  it("builds option from frequency data", () => {
    const opt = buildFrequencyOption(report, "dept", "bar");
    expect(opt.xAxis.data).toEqual(["Eng", "Sales"]);
    expect(opt.series[0].data).toEqual([5, 3]);
  });
  it("returns null for missing field", () => {
    expect(buildFrequencyOption(report, "missing", "bar")).toBeNull();
  });
});

describe("buildParetoOption", () => {
  const report = {
    pareto: { sales: [{ value: 100, count: 100, cum_pct: 0.5 }, { value: 50, count: 150, cum_pct: 0.75 }] },
  };
  it("builds pareto with dual axes", () => {
    const opt = buildParetoOption(report, "sales");
    expect(opt.yAxis).toHaveLength(2);
    expect(opt.series[0].type).toBe("bar");
    expect(opt.series[1].type).toBe("line");
  });
});

describe("buildBoxplotOption", () => {
  const report = {
    boxplot: { age: { min: 20, q1: 25, median: 30, q3: 35, max: 40, outliers: [45, 18] } },
  };
  it("builds boxplot with scatter outliers", () => {
    const opt = buildBoxplotOption(report);
    expect(opt.series[0].type).toBe("boxplot");
    expect(opt.series[1].type).toBe("scatter");
  });
});

describe("buildCorrelationOption", () => {
  const report = {
    correlation: { fields: ["a", "b"], matrix: [[1, 0.5], [0.5, 1]] },
  };
  it("builds heatmap", () => {
    const opt = buildCorrelationOption(report);
    expect(opt.series[0].type).toBe("heatmap");
    expect(opt.xAxis.data).toEqual(["a", "b"]);
  });
  it("returns null without fields", () => {
    expect(buildCorrelationOption({ correlation: {} })).toBeNull();
  });
});

describe("buildGroupStatsOption", () => {
  const report = {
    group_stats: {
      categorical_fields: ["dept"],
      numeric_fields: ["salary"],
      data: { dept: { Engineering: { salary: { mean: 60000 } }, Sales: { salary: { mean: 50000 } } } },
    },
  };
  it("builds grouped bar chart", () => {
    const opt = buildGroupStatsOption(report, "dept", "mean");
    expect(opt.series[0].data).toEqual([60000, 50000]);
    expect(opt.xAxis.data).toEqual(["Engineering", "Sales"]);
  });
  it("returns null for missing group", () => {
    expect(buildGroupStatsOption(report, "missing", "mean")).toBeNull();
  });
});

describe("buildBinningOption", () => {
  const report = {
    binning: { age: { equal_width: { bins: [0, 20, 40], counts: [3, 7] } } },
  };
  it("builds binning bar chart", () => {
    const opt = buildBinningOption(report, "age", "equal_width");
    expect(opt.series[0].type).toBe("bar");
    expect(opt.xAxis.data).toHaveLength(2);
  });
  it("returns null for missing field", () => {
    expect(buildBinningOption(report, "missing", "equal_width")).toBeNull();
  });
});

describe("buildViolinOption", () => {
  const report = {
    violin: { age: { density_x: [1, 2, 3], density_y: [0.1, 0.5, 0.1], min: 1, max: 3, mean: 2 } },
  };
  it("builds violin series", () => {
    const opt = buildViolinOption(report, "age");
    expect(opt.series).toHaveLength(4);
  });
});

describe("buildScatterOption", () => {
  const report = {
    scatter_matrix: {
      fields: ["x", "y"],
      data: [{ x: 1, y: 2 }, { x: 3, y: 4 }],
    },
  };
  it("builds scatter plot", () => {
    const opt = buildScatterOption(report, "x", "y");
    expect(opt.series[0].type).toBe("scatter");
  });
  it("returns null without fields", () => {
    expect(buildScatterOption(report, "", "")).toBeNull();
  });
});

describe("buildMissingHeatmapOption", () => {
  const report = {
    missing_heatmap: {
      fields: ["a", "b"],
      rows: 3,
      total_rows: 3,
      sampled: false,
      data: [[true, false], [false, true], [false, false]],
    },
  };
  it("builds heatmap", () => {
    const opt = buildMissingHeatmapOption(report);
    expect(opt.series[0].type).toBe("heatmap");
    expect(opt.xAxis.data).toEqual(["a", "b"]);
  });
  it("returns null for empty data", () => {
    expect(buildMissingHeatmapOption({ missing_heatmap: { data: [] } })).toBeNull();
  });
});

describe("buildTimeseriesOption", () => {
  const report = {
    timeseries: {
      date: { daily: { dates: ["2024-01-01", "2024-01-02"], values: [5, 10] } },
    },
  };
  it("builds line chart", () => {
    const opt = buildTimeseriesOption(report, "date", "daily");
    expect(opt.series[0].type).toBe("line");
    expect(opt.xAxis.data).toEqual(["2024-01-01", "2024-01-02"]);
  });
  it("returns null for missing period", () => {
    expect(buildTimeseriesOption(report, "date", "yearly")).toBeNull();
  });
});

describe("buildOutliersOption", () => {
  const report = {
    outliers: { age: { iqr: { count: 2 }, zscore: { count: 1 } } },
  };
  it("builds bar chart with IQR/ZScore counts", () => {
    const opt = buildOutliersOption(report, "age");
    expect(opt.series[0].data).toEqual([2, 1]);
  });
});

describe("buildComparisonHistogramOption", () => {
  const report = {
    histograms: {
      age: { bins: [0, 10, 20], counts: [2, 3] },
      salary: { bins: [0, 50, 100], counts: [1, 4] },
    },
  };
  it("builds multi-series bar chart", () => {
    const opt = buildComparisonHistogramOption(report, ["age", "salary"]);
    expect(opt.series).toHaveLength(2);
    expect(opt.series[0].type).toBe("bar");
  });
  it("returns null for empty fields", () => {
    expect(buildComparisonHistogramOption(report, [])).toBeNull();
  });
});
