import { describe, it, expect, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { useI18n } from "../composables/useI18n";

import SettingsMenu from "../components/SettingsMenu.vue";
import PreviewCard from "../components/PreviewCard.vue";
import ReportSection from "../components/ReportSection.vue";
import FilterPanel from "../components/FilterPanel.vue";
import SelectionDialog from "../components/SelectionDialog.vue";
import ChartSetupDialog from "../components/ChartSetupDialog.vue";
import ChartToolbar from "../components/ChartToolbar.vue";

beforeEach(() => {
  const { setLanguage } = useI18n();
  setLanguage("zh");
});

describe("SettingsMenu", () => {
  it("renders without props", () => {
    const wrapper = mount(SettingsMenu, { props: { show: false, locale: "zh", selectionMode: "dialog" } });
    expect(wrapper.exists()).toBe(true);
  });

  it("shows dropdown when show is true", () => {
    const wrapper = mount(SettingsMenu, { props: { show: true, locale: "zh", selectionMode: "dialog" } });
    expect(wrapper.find(".lang-dropdown").exists()).toBe(true);
  });

  it("emits toggle on button click", () => {
    const wrapper = mount(SettingsMenu, { props: { show: false, locale: "zh", selectionMode: "dialog" } });
    wrapper.find(".lang-button").trigger("click");
    expect(wrapper.emitted("toggle")).toBeTruthy();
  });

  it("emits update:locale when clicking language option", () => {
    const wrapper = mount(SettingsMenu, { props: { show: true, locale: "zh", selectionMode: "dialog" } });
    const btns = wrapper.findAll(".lang-option");
    const enBtn = btns.find((b) => b.text().includes("English"));
    if (enBtn) enBtn.trigger("click");
    expect(wrapper.emitted("update:locale")).toBeTruthy();
  });
});

describe("PreviewCard", () => {
  const mockPreview = {
    filename: "test.csv",
    rows: 100,
    columns: 5,
  };

  it("renders with preview data", () => {
    const wrapper = mount(PreviewCard, {
      props: {
        preview: mockPreview,
        showAllFields: false,
        totalFields: 5,
        visibleFields: ["a", "b"],
        hasMoreFields: false,
      },
    });
    expect(wrapper.text()).toContain("test.csv");
    expect(wrapper.text()).toContain("100");
    expect(wrapper.text()).toContain("5");
  });

  it("shows field chips when fields exist", () => {
    const wrapper = mount(PreviewCard, {
      props: {
        preview: mockPreview,
        showAllFields: false,
        totalFields: 2,
        visibleFields: ["a", "b"],
        hasMoreFields: false,
      },
    });
    expect(wrapper.find(".field-chip").exists()).toBe(true);
  });

  it("does not render when preview is null", () => {
    const wrapper = mount(PreviewCard, {
      props: {
        preview: null,
        showAllFields: false,
        totalFields: 0,
        visibleFields: [],
        hasMoreFields: false,
      },
    });
    expect(wrapper.find(".hero-card").exists()).toBe(false);
  });

  it("emits toggleFields when button clicked", () => {
    const wrapper = mount(PreviewCard, {
      props: {
        preview: mockPreview,
        showAllFields: false,
        totalFields: 10,
        visibleFields: ["a"],
        hasMoreFields: true,
      },
    });
    const btn = wrapper.find(".fields-toggle");
    expect(btn.exists()).toBe(true);
    btn.trigger("click");
    expect(wrapper.emitted("toggleFields")).toBeTruthy();
  });
});

describe("ReportSection", () => {
  const mockReportData = {
    dtypes: { name: "object", age: "int64" },
  };

  const mockStatsRows = [
    { field: "name", dtype: "object", missing: 0, missingRate: 0, count: null, mean: null, std: null, min: null, max: null },
    { field: "age", dtype: "int64", missing: 0, missingRate: 0, count: 2, mean: 27.5, std: 3.5, min: 25, max: 30 },
  ];

  it("renders report title", () => {
    const wrapper = mount(ReportSection, {
      props: { reportData: mockReportData, showSample: false, sampleRows: [], sampleColumns: [], statsRows: mockStatsRows },
    });
    expect(wrapper.find(".report-section").exists()).toBe(true);
  });

  it("renders stats table rows", () => {
    const wrapper = mount(ReportSection, {
      props: { reportData: mockReportData, showSample: false, sampleRows: [], sampleColumns: [], statsRows: mockStatsRows },
    });
    expect(wrapper.text()).toContain("name");
    expect(wrapper.text()).toContain("age");
  });

  it("shows sample section when showSample is true", () => {
    const wrapper = mount(ReportSection, {
      props: {
        reportData: mockReportData,
        showSample: true,
        sampleRows: [{ name: "Alice", age: 25 }],
        sampleColumns: ["name", "age"],
        statsRows: mockStatsRows,
      },
    });
    expect(wrapper.text()).toContain("Alice");
  });

  it("shows empty state when no reportData", () => {
    const wrapper = mount(ReportSection, {
      props: { reportData: null, showSample: false, sampleRows: [], sampleColumns: [], statsRows: [] },
    });
    expect(wrapper.find(".empty-state").exists()).toBe(true);
  });

  it("formats missing rate as percentage", () => {
    const rows = [{ field: "x", dtype: "object", missing: 1, missingRate: 0.25, count: null, mean: null, std: null, min: null, max: null }];
    const wrapper = mount(ReportSection, {
      props: { reportData: { dtypes: { x: "object" } }, showSample: false, sampleRows: [], sampleColumns: [], statsRows: rows },
    });
    expect(wrapper.text()).toContain("25.0%");
  });

  it("formats null values as dash", () => {
    const rows = [{ field: "x", dtype: "object", missing: 0, missingRate: 0, count: null, mean: null, std: null, min: null, max: null }];
    const wrapper = mount(ReportSection, {
      props: { reportData: { dtypes: { x: "object" } }, showSample: false, sampleRows: [], sampleColumns: [], statsRows: rows },
    });
    expect(wrapper.text()).toContain("-");
  });
});

describe("FilterPanel", () => {
  it("renders when showFilterPanel is true", () => {
    const wrapper = mount(FilterPanel, {
      props: {
        showFilterPanel: true,
        filterInfo: {},
        ranges: {},
        allFields: ["a", "b"],
        selectedFields: null,
      },
    });
    expect(wrapper.find(".selection-overlay").exists()).toBe(true);
  });

  it("does not render when showFilterPanel is false", () => {
    const wrapper = mount(FilterPanel, {
      props: {
        showFilterPanel: false,
        filterInfo: {},
        ranges: {},
        allFields: [],
        selectedFields: null,
      },
    });
    expect(wrapper.find(".selection-overlay").exists()).toBe(false);
  });

  it("shows field checkboxes", () => {
    const wrapper = mount(FilterPanel, {
      props: {
        showFilterPanel: true,
        filterInfo: {},
        ranges: {},
        allFields: ["name", "age"],
        selectedFields: ["name", "age"],
      },
    });
    const checkboxes = wrapper.findAll('input[type="checkbox"]');
    expect(checkboxes.length).toBeGreaterThanOrEqual(2);
  });

  it("emits apply on button click", () => {
    const wrapper = mount(FilterPanel, {
      props: {
        showFilterPanel: true,
        filterInfo: {},
        ranges: {},
        allFields: ["a"],
        selectedFields: null,
      },
    });
    wrapper.find(".primary-btn").trigger("click");
    expect(wrapper.emitted("apply")).toBeTruthy();
  });

  it("emits reset on reset button click", () => {
    const wrapper = mount(FilterPanel, {
      props: {
        showFilterPanel: true,
        filterInfo: {},
        ranges: {},
        allFields: ["a"],
        selectedFields: null,
      },
    });
    wrapper.find(".ghost-button").trigger("click");
    expect(wrapper.emitted("reset")).toBeTruthy();
  });

  it("emits close on overlay click", () => {
    const wrapper = mount(FilterPanel, {
      props: {
        showFilterPanel: true,
        filterInfo: {},
        ranges: {},
        allFields: ["a"],
        selectedFields: null,
      },
    });
    wrapper.find(".selection-overlay").trigger("click");
    expect(wrapper.emitted("close")).toBeTruthy();
  });
});

describe("SelectionDialog", () => {
  const defaultSelection = { preview: true, report: true, sample: false, charts_enabled: true };

  it("renders when show is true", () => {
    const wrapper = mount(SelectionDialog, {
      props: { show: true, selection: defaultSelection, selectionMode: "dialog", disabled: false },
    });
    expect(wrapper.find(".selection-overlay").exists()).toBe(true);
  });

  it("does not render when show is false", () => {
    const wrapper = mount(SelectionDialog, {
      props: { show: false, selection: defaultSelection, selectionMode: "dialog", disabled: false },
    });
    expect(wrapper.find(".selection-overlay").exists()).toBe(false);
  });

  it("emits confirm on primary button click", () => {
    const wrapper = mount(SelectionDialog, {
      props: { show: true, selection: defaultSelection, selectionMode: "dialog", disabled: false },
    });
    wrapper.find(".primary-btn").trigger("click");
    expect(wrapper.emitted("confirm")).toBeTruthy();
  });

  it("emits close on cancel button click", () => {
    const wrapper = mount(SelectionDialog, {
      props: { show: true, selection: defaultSelection, selectionMode: "dialog", disabled: false },
    });
    wrapper.find(".ghost-button").trigger("click");
    expect(wrapper.emitted("close")).toBeTruthy();
  });
});

describe("ChartSetupDialog", () => {
  const defaultChartTypes = {
    missing_rate: true, feature_distribution: true, numeric_mean: false,
    numeric_max: false, numeric_min: false, dtype_distribution: true,
    frequency: false, pareto: false, boxplot: false, correlation: false,
    group_stats: false, binning: false, violin: false, scatter_matrix: false,
    missing_heatmap: false, timeseries: false, outliers: false,
  };

  it("renders when show is true", () => {
    const wrapper = mount(ChartSetupDialog, {
      props: { show: true, chartTypes: defaultChartTypes, selectionMode: "dialog" },
    });
    expect(wrapper.find(".selection-overlay").exists()).toBe(true);
  });

  it("emits confirm on button click", () => {
    const wrapper = mount(ChartSetupDialog, {
      props: { show: true, chartTypes: defaultChartTypes, selectionMode: "dialog" },
    });
    wrapper.find(".primary-btn").trigger("click");
    expect(wrapper.emitted("confirm")).toBeTruthy();
  });

  it("emits update:chartTypes on toggle", () => {
    const wrapper = mount(ChartSetupDialog, {
      props: { show: true, chartTypes: defaultChartTypes, selectionMode: "dialog" },
    });
    const checkbox = wrapper.findAll('input[type="checkbox"]')[1];
    checkbox.trigger("change");
    expect(wrapper.emitted("update:chartTypes")).toBeTruthy();
  });
});

describe("ChartToolbar", () => {
  it("renders toolbar buttons when hasCharts is true", () => {
    const wrapper = mount(ChartToolbar, {
      props: { showOptions: true, hasCharts: true, title: "Test Chart", showFilter: false, comparisonMode: false },
    });
    expect(wrapper.find(".chart-toolbar").exists()).toBe(true);
    expect(wrapper.text()).toContain("Test Chart");
  });

  it("disables toggle when hasCharts is false", () => {
    const wrapper = mount(ChartToolbar, {
      props: { showOptions: true, hasCharts: false, title: "", showFilter: false, comparisonMode: false },
    });
    const toggle = wrapper.find(".chart-options-toggle");
    expect(toggle.attributes("disabled")).toBeDefined();
  });

  it("emits events on button clicks", () => {
    const wrapper = mount(ChartToolbar, {
      props: { showOptions: true, hasCharts: true, title: "Chart", showFilter: false, comparisonMode: false },
    });
    wrapper.find(".chart-options-toggle").trigger("click");
    expect(wrapper.emitted("toggleOptions")).toBeTruthy();
  });
});
