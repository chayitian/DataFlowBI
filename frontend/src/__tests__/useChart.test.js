import { describe, it, expect, beforeEach, vi } from "vitest";
import { ref } from "vue";
import { useChart } from "../composables/useChart";
import { useI18n } from "../composables/useI18n";

describe("useChart", () => {
  let activeReport;
  let savedName;
  let chart;

  beforeEach(() => {
    vi.restoreAllMocks();
    const { setLanguage } = useI18n();
    setLanguage("zh");

    activeReport = ref(null);
    savedName = ref("");

    const options = {
      activeReport,
      savedName,
      analysisOptions: ref([
        { key: "missing_rate", label: "Missing Rate" },
        { key: "feature_distribution", label: "Feature Distribution" },
        { key: "dtype_distribution", label: "Type Distribution" },
      ]),
    };

    chart = useChart(options);
    chart.resetChart();
  });

  it("hasChartData returns false without report", () => {
    expect(chart.hasChartData.value).toBe(false);
  });

  it("chartCategory defaults to null", () => {
    expect(chart.chartCategory.value).toBeNull();
  });

  it("selectAnalysis sets category and syncs", () => {
    activeReport.value = { missing_rate: { a: 0.1, b: 0.2 } };
    chart.selectAnalysis("missing_rate");
    expect(chart.chartCategory.value).toBe("missing_rate");
  });

  it("syncChartSelection picks first available for current category", () => {
    activeReport.value = {
      dtypes: { a: "object", b: "int64" },
      missing_rate: { a: 0.1 },
      histograms: { age: { bins: [0, 10], counts: [5] } },
    };
    chart.selectAnalysis("missing_rate");
    expect(chart.chartCategory.value).toBe("missing_rate");

    chart.syncChartSelection();
    expect(chart.chartType.value).toBe("bar");
  });

  it("buildChartOption returns null without report", () => {
    const opt = chart.buildChartOption(null, "missing_rate", "bar", "field");
    expect(opt).toBeNull();
  });

  it("buildChartOption dispatches to correct builder", () => {
    const report = { missing_rate: { a: 0.1 } };
    const opt = chart.buildChartOption(report, "missing_rate", "bar", null);
    expect(opt).not.toBeNull();
    expect(opt.series[0].type).toBe("bar");
  });

  it("buildChartOption returns null for unknown category", () => {
    const opt = chart.buildChartOption({}, "unknown_category", "bar", null);
    expect(opt).toBeNull();
  });

  it("currentChartTitle shows category label", () => {
    activeReport.value = { missing_rate: { a: 0.1 } };
    chart.selectAnalysis("missing_rate");
    expect(chart.currentChartTitle.value).toBe("Missing Rate · 柱状图");
  });

  it("resetChart clears all state", () => {
    chart.chartCategory.value = "missing_rate";
    chart.chartFeature.value = "age";
    chart.histogramBinCount.value = 20;
    chart.histogramNormalize.value = true;
    chart.comparisonMode.value = true;
    chart.selectedComparisonFields.value = ["a", "b"];

    chart.resetChart();

    expect(chart.chartCategory.value).toBeNull();
    expect(chart.chartFeature.value).toBeNull();
    expect(chart.histogramBinCount.value).toBe(10);
    expect(chart.histogramNormalize.value).toBe(false);
    expect(chart.comparisonMode.value).toBe(false);
    expect(chart.selectedComparisonFields.value).toEqual([]);
  });

  it("selectChartType changes type", () => {
    chart.selectChartType("line");
    expect(chart.chartType.value).toBe("line");
  });

  it("selectFeature changes feature", () => {
    chart.selectFeature("age");
    expect(chart.chartFeature.value).toBe("age");
  });

  it("toggleComparisonField adds and removes fields", () => {
    chart.toggleComparisonField("a");
    expect(chart.selectedComparisonFields.value).toContain("a");

    chart.toggleComparisonField("b");
    expect(chart.selectedComparisonFields.value).toHaveLength(2);

    chart.toggleComparisonField("a");
    expect(chart.selectedComparisonFields.value).not.toContain("a");
    expect(chart.selectedComparisonFields.value).toHaveLength(1);
  });
});
