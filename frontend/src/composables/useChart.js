import { ref, computed, nextTick } from "vue";
import { rebinHistogram as rebinApi } from "../api/upload";
import { useI18n } from "./useI18n";
import {
  buildHistogramOption, buildNumericOption, buildMissingRateOption,
  buildTypeDistributionOption, buildFrequencyOption, buildParetoOption,
  buildBoxplotOption, buildCorrelationOption, buildGroupStatsOption,
  buildBinningOption, buildViolinOption, buildScatterOption,
  buildMissingHeatmapOption, buildTimeseriesOption, buildOutliersOption,
  buildComparisonHistogramOption,
} from "./chartBuilders";

const { t } = useI18n();

let echartsPromise = null;
const getECharts = () => {
  // ECharts 体积较大，因此首次渲染图表时才懒加载。
  if (!echartsPromise) echartsPromise = import("echarts");
  return echartsPromise;
};

let isRendering = false;
const chartCategory = ref(null);
const chartType = ref("bar");
const chartFeature = ref(null);
const chartEl = ref(null);
const chartInstance = ref(null);
const histogramBinCount = ref(10);
const histogramNormalize = ref(false);
const rebinData = ref(null);
const histogramDefaultBinCount = 8;
const groupAggregation = ref("mean");
const binningMethod = ref("equal_width");
const scatterXField = ref("");
const scatterYField = ref("");
const timeseriesPeriod = ref("daily");
const comparisonMode = ref(false);
const selectedComparisonFields = ref([]);

export function useChart(opts = {}) {
  const { activeReport, savedName } = opts;

  // 这些 computed 列表表示当前报告实际支持哪些图表类型。
  // 选项面板使用它们避免出现空选择。
  const histogramFeatures = computed(() => Object.keys(activeReport?.value?.histograms || {}));
  const frequencyFields = computed(() => Object.keys(activeReport?.value?.frequencies || {}));
  const paretoFields = computed(() => Object.keys(activeReport?.value?.pareto || {}));
  const boxplotFields = computed(() => Object.keys(activeReport?.value?.boxplot || {}));
  const groupCategoricalFields = computed(() => activeReport?.value?.group_stats?.categorical_fields || []);
  const binningFields = computed(() => Object.keys(activeReport?.value?.binning || {}));
  const violinFields = computed(() => Object.keys(activeReport?.value?.violin || {}));
  const scatterFields = computed(() => activeReport?.value?.scatter_matrix?.fields || []);
  const timeseriesFields = computed(() => Object.keys(activeReport?.value?.timeseries || {}));
  const outlierFields = computed(() => Object.keys(activeReport?.value?.outliers || {}));

  const buildChartOption = (report, category, type, feature) => {
    // 把选中的分析类别路由到对应的 ECharts option builder。
    if (!report || !category) return null;
    if (category === "missing_rate") return buildMissingRateOption(report, type);
    if (category === "feature_distribution") {
      if (comparisonMode.value && selectedComparisonFields.value.length > 1)
        return buildComparisonHistogramOption(report, selectedComparisonFields.value);
      let histData = report;
      if (rebinData.value && rebinData.value.field === feature) {
        histData = { histograms: { [feature]: { bins: rebinData.value.bins, counts: rebinData.value.counts } } };
      }
      return buildHistogramOption(histData, feature);
    }
    if (category === "violin") return buildViolinOption(report, feature);
    if (category === "scatter_matrix") return buildScatterOption(report, scatterXField.value, scatterYField.value);
    if (category === "missing_heatmap") return buildMissingHeatmapOption(report);
    if (category === "timeseries") return buildTimeseriesOption(report, feature, timeseriesPeriod.value);
    if (category === "outliers") return buildOutliersOption(report, feature);
    if (category === "correlation") return buildCorrelationOption(report);
    if (category === "boxplot") return buildBoxplotOption(report);
    if (category === "group_stats") return buildGroupStatsOption(report, feature, groupAggregation.value);
    if (category === "binning") return buildBinningOption(report, feature, binningMethod.value);
    if (category === "frequency") return buildFrequencyOption(report, feature, type);
    if (category === "pareto") return buildParetoOption(report, feature);
    if (category === "dtype_distribution") return buildTypeDistributionOption(report, type);
    if (category === "numeric_mean") return buildNumericOption(report, "mean", type);
    if (category === "numeric_max") return buildNumericOption(report, "max", type);
    if (category === "numeric_min") return buildNumericOption(report, "min", type);
    return null;
  };

  const chartOption = computed(() => {
    // 显式读取这些 ref，确保图表控制项变化时 Vue 会重新计算。
    rebinData.value; groupAggregation.value; binningMethod.value;
    scatterXField.value; scatterYField.value; timeseriesPeriod.value;
    comparisonMode.value; selectedComparisonFields.value;
    return buildChartOption(activeReport?.value, chartCategory.value, chartType.value, chartFeature.value);
  });

  const hasChartData = computed(() => Boolean(chartOption.value));

  const currentChartTitle = computed(() => {
    if (!chartCategory.value) return t("chartEmpty");
    const options = opts.analysisOptions?.value || [];
    const active = options.find(o => o.key === chartCategory.value);
    const label = active?.label || chartCategory.value;
    if (chartCategory.value === "feature_distribution") return `${label} · ${t("chartTypeHistogram")}${chartFeature.value ? ` · ${chartFeature.value}` : ""}`;
    if (chartCategory.value === "frequency") return `${label}${chartFeature.value ? ` · ${chartFeature.value}` : ""}`;
    if (chartCategory.value === "violin") return `${label}${chartFeature.value ? ` · ${chartFeature.value}` : ""}`;
    if (chartCategory.value === "scatter_matrix") return `${label} · ${scatterXField.value || "?"} × ${scatterYField.value || "?"}`;
    if (chartCategory.value === "missing_heatmap") return `${label} · ${t("chartTypeMissingHeatmap")}`;
    if (chartCategory.value === "timeseries") return `${label}${chartFeature.value ? ` · ${chartFeature.value}` : ""} · ${timeseriesPeriod.value === "daily" ? t("timeseriesDaily") : timeseriesPeriod.value === "monthly" ? t("timeseriesMonthly") : t("timeseriesYearly")}`;
    if (chartCategory.value === "outliers") return `${label}${chartFeature.value ? ` · ${chartFeature.value}` : ""}`;
    if (chartCategory.value === "boxplot") return `${label} · ${t("chartTypeBoxplot")}`;
    if (chartCategory.value === "correlation") return `${label} · ${t("chartTypeCorrelation")}`;
    if (chartCategory.value === "group_stats") return `${label}${chartFeature.value ? ` · ${chartFeature.value}` : ""} · ${t("groupAgg" + groupAggregation.value.charAt(0).toUpperCase() + groupAggregation.value.slice(1))}`;
    if (chartCategory.value === "binning") return `${label}${chartFeature.value ? ` · ${chartFeature.value}` : ""} · ${binningMethod.value === "equal_width" ? t("binningEqualWidth") : t("binningEqualFreq")}`;
    if (chartCategory.value === "pareto") return `${label}${chartFeature.value ? ` · ${chartFeature.value}` : ""}`;
    const typeLabel = chartType.value === "line" ? t("chartTypeLine") : t("chartTypeBar");
    return `${label} · ${typeLabel}`;
  });

  const renderChart = async () => {
    // ECharts 是动态加载的，因此渲染流程是异步的。
    if (isRendering) return;
    isRendering = true;
    try {
      if (!chartEl.value) return;
      if (!chartOption.value) {
        if (chartInstance.value) chartInstance.value.clear();
        return;
      }
      if (!chartInstance.value) {
        const echarts = await getECharts();
        chartInstance.value = echarts.init(chartEl.value);
      }
      chartInstance.value.setOption(chartOption.value, true);
    } finally {
      isRendering = false;
    }
  };

  const resizeChart = () => { if (chartInstance.value) chartInstance.value.resize(); };

  const syncChartSelection = () => {
    // 新报告到达时，如果现有选择仍有效就保留，否则选择第一个有效类别/字段。
    if (!opts.analysisOptions?.value?.length) {
      chartCategory.value = null; chartType.value = "bar"; chartFeature.value = null;
      return;
    }
    if (!opts.analysisOptions.value.some((o) => o.key === chartCategory.value))
      chartCategory.value = opts.analysisOptions.value[0].key;
    if (chartCategory.value === "feature_distribution") {
      chartType.value = "histogram";
      if (!histogramFeatures.value.includes(chartFeature.value)) chartFeature.value = histogramFeatures.value[0] || null;
    } else if (chartCategory.value === "frequency") {
      chartType.value = "bar";
      if (!frequencyFields.value.includes(chartFeature.value)) chartFeature.value = frequencyFields.value[0] || null;
    } else if (chartCategory.value === "violin") {
      chartType.value = "bar";
      if (!violinFields.value.includes(chartFeature.value)) chartFeature.value = violinFields.value[0] || null;
    } else if (chartCategory.value === "scatter_matrix") {
      chartType.value = "bar";
      const sf = scatterFields.value;
      if (!sf.includes(scatterXField.value)) scatterXField.value = sf[0] || "";
      if (!sf.includes(scatterYField.value) || scatterYField.value === scatterXField.value) scatterYField.value = sf[1] || sf[0] || "";
      chartFeature.value = null;
    } else if (chartCategory.value === "missing_heatmap" || chartCategory.value === "boxplot" || chartCategory.value === "correlation") {
      chartType.value = "bar"; chartFeature.value = null;
    } else if (chartCategory.value === "timeseries") {
      chartType.value = "bar";
      if (!timeseriesFields.value.includes(chartFeature.value)) chartFeature.value = timeseriesFields.value[0] || null;
    } else if (chartCategory.value === "outliers") {
      chartType.value = "bar";
      if (!outlierFields.value.includes(chartFeature.value)) chartFeature.value = outlierFields.value[0] || null;
    } else if (chartCategory.value === "group_stats") {
      chartType.value = "bar";
      if (!groupCategoricalFields.value.includes(chartFeature.value)) chartFeature.value = groupCategoricalFields.value[0] || null;
    } else if (chartCategory.value === "binning") {
      chartType.value = "bar";
      if (!binningFields.value.includes(chartFeature.value)) chartFeature.value = binningFields.value[0] || null;
    } else if (chartCategory.value === "pareto") {
      chartType.value = "bar";
      if (!paretoFields.value.includes(chartFeature.value)) chartFeature.value = paretoFields.value[0] || null;
    } else {
      if (!["bar", "line"].includes(chartType.value)) chartType.value = "bar";
      chartFeature.value = null;
    }
  };

  const selectAnalysis = (key) => { chartCategory.value = key; syncChartSelection(); };
  const selectChartType = (type) => { chartType.value = type; };
  const selectFeature = (feature) => { chartFeature.value = feature; };
  const toggleComparisonField = (field) => {
    const idx = selectedComparisonFields.value.indexOf(field);
    if (idx >= 0) selectedComparisonFields.value.splice(idx, 1);
    else selectedComparisonFields.value.push(field);
  };

  const rebin = async () => {
    // 重新分箱会要求后端基于原始缓存数据重新计算直方图分箱。
    if (!savedName?.value || !chartFeature.value || chartCategory.value !== "feature_distribution") return;
    try {
      rebinData.value = await rebinApi(savedName.value, chartFeature.value, histogramBinCount.value, histogramNormalize.value);
    } catch { rebinData.value = null; }
  };

  const downloadChart = (format) => {
    // 直接在浏览器下载当前渲染的 ECharts canvas/SVG。
    if (!chartInstance.value) return;
    const url = chartInstance.value.getDataURL({ type: format === "svg" ? "svg" : "png", pixelRatio: 2, backgroundColor: "#fff" });
    const link = document.createElement("a");
    link.download = `dataflowbi_chart.${format}`;
    link.href = url;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const resetChart = () => {
    chartCategory.value = null;
    chartFeature.value = null;
    rebinData.value = null;
    histogramBinCount.value = 10;
    histogramNormalize.value = false;
    groupAggregation.value = "mean";
    binningMethod.value = "equal_width";
    scatterXField.value = "";
    scatterYField.value = "";
    timeseriesPeriod.value = "daily";
    comparisonMode.value = false;
    selectedComparisonFields.value = [];
  };

  return {
    chartCategory, chartType, chartFeature, chartEl, chartInstance,
    histogramBinCount, histogramNormalize, rebinData, groupAggregation, binningMethod,
    scatterXField, scatterYField, timeseriesPeriod, comparisonMode, selectedComparisonFields,
    histogramFeatures, frequencyFields, paretoFields, boxplotFields, groupCategoricalFields,
    binningFields, violinFields, scatterFields, timeseriesFields, outlierFields,
    chartOption, hasChartData, currentChartTitle,
    renderChart, resizeChart, syncChartSelection, selectAnalysis, selectChartType,
    selectFeature, toggleComparisonField, rebin, downloadChart,
    resetChart, buildChartOption,
  };
}
