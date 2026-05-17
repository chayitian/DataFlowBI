import { ref, computed } from "vue";
import { useI18n } from "./useI18n";

const buildDefaultSelection = () => ({
  preview: true,
  report: true,
  sample: false,
  charts_enabled: true,
});

const buildDefaultChartTypes = () => ({
  missing_rate: true,
  feature_distribution: true,
  numeric_mean: false,
  numeric_max: false,
  numeric_min: false,
  dtype_distribution: true,
  frequency: false,
  pareto: false,
  boxplot: false,
  correlation: false,
  group_stats: false,
  binning: false,
  violin: false,
  scatter_matrix: false,
  missing_heatmap: false,
  timeseries: false,
  outliers: false,
});

const selection = ref(buildDefaultSelection());
const appliedSelection = ref(buildDefaultSelection());
const chartConfigApplied = ref(false);
const showChartSetup = ref(false);
const tempChartTypes = ref(buildDefaultChartTypes());
const appliedChartTypes = ref(buildDefaultChartTypes());
const showSelection = ref(false);
const showChartOptions = ref(false);

export function useSelection(opts = {}) {
  const { t } = useI18n();
  const { runUpload, hasParsedRef, isUploadingRef } = opts;

  const hasSelectedCharts = computed(() => {
    const charts = chartConfigApplied.value ? appliedChartTypes.value : {};
    return Object.values(charts).some(Boolean);
  });

  const showPreviewCard = computed(
    () => hasParsedRef?.value && appliedSelection.value?.preview
  );
  const showReportSection = computed(
    () => hasParsedRef?.value && appliedSelection.value?.report
  );
  const showSampleSection = computed(
    () => showReportSection.value && appliedSelection.value?.sample
  );
  const showChartSection = computed(
    () => hasParsedRef?.value && appliedSelection.value?.charts_enabled && chartConfigApplied.value && hasSelectedCharts.value
  );

  const analysisOptions = computed(() => {
    const charts = chartConfigApplied.value ? appliedChartTypes.value : {};
    const options = [
      { key: "missing_rate", label: t("analysisMissingRate") },
      { key: "feature_distribution", label: t("analysisFeatureDistribution") },
      { key: "violin", label: t("analysisViolin") },
      { key: "scatter_matrix", label: t("analysisScatter") },
      { key: "missing_heatmap", label: t("analysisMissingHeatmap") },
      { key: "timeseries", label: t("analysisTimeseries") },
      { key: "outliers", label: t("analysisOutliers") },
      { key: "boxplot", label: t("analysisBoxplot") },
      { key: "correlation", label: t("analysisCorrelation") },
      { key: "group_stats", label: t("analysisGroupStats") },
      { key: "binning", label: t("analysisBinning") },
      { key: "frequency", label: t("analysisFrequency") },
      { key: "pareto", label: t("analysisPareto") },
      { key: "dtype_distribution", label: t("analysisTypeDistribution") },
      { key: "numeric_mean", label: t("analysisNumericMean") },
      { key: "numeric_max", label: t("analysisNumericMax") },
      { key: "numeric_min", label: t("analysisNumericMin") },
    ];
    return options.filter((option) => charts[option.key]);
  });

  const normalizeSelection = (value) => {
    const normalized = {
      preview: Boolean(value.preview),
      report: Boolean(value.report),
      sample: Boolean(value.sample) && Boolean(value.report),
      charts_enabled: Boolean(value.charts_enabled),
    };
    if (!normalized.report) normalized.sample = false;
    return normalized;
  };

  const cloneSelection = (value) => JSON.parse(JSON.stringify(value));

  const openSelection = () => {
    if (isUploadingRef?.value) return;
    selection.value = cloneSelection(appliedSelection.value);
    showSelection.value = true;
  };

  const closeSelection = () => { showSelection.value = false; };

  const initTempChartTypes = () => {
    const source = chartConfigApplied.value ? appliedChartTypes.value : buildDefaultChartTypes();
    tempChartTypes.value = JSON.parse(JSON.stringify(source));
  };

  const confirmChartSetup = () => {
    appliedChartTypes.value = { ...tempChartTypes.value };
    chartConfigApplied.value = true;
    showChartSetup.value = false;
    showChartOptions.value = false;
  };

  const openChartSetup = () => {
    initTempChartTypes();
    showChartSetup.value = true;
  };

  const closeChartSetup = () => { showChartSetup.value = false; };

  const confirmSelection = async () => {
    const normalized = normalizeSelection(selection.value);
    appliedSelection.value = normalized;
    showSelection.value = false;
    showChartOptions.value = false;
    if (runUpload) await runUpload();
    if (normalized.charts_enabled && !chartConfigApplied.value) {
      appliedChartTypes.value = { ...buildDefaultChartTypes() };
      chartConfigApplied.value = true;
    }
  };

  return {
    buildDefaultChartTypes,
    selection, appliedSelection, chartConfigApplied, showChartSetup,
    tempChartTypes, appliedChartTypes, showSelection, showChartOptions,
    hasSelectedCharts, showPreviewCard, showReportSection, showSampleSection,
    showChartSection, analysisOptions,
    openSelection, closeSelection, confirmSelection,
    openChartSetup, closeChartSetup, confirmChartSetup, initTempChartTypes,
    normalizeSelection, cloneSelection,
  };
}
