<template>
  <div class="page">
    <SettingsMenu
      :show="showSettingsMenu"
      :locale="locale"
      :selectionMode="selectionMode"
      @toggle="showSettingsMenu = !showSettingsMenu"
      @update:locale="setLanguage($event); showSettingsMenu = false"
      @update:selectionMode="selectionMode = $event; showSettingsMenu = false"
    />
    <button class="history-btn" title="History" @click="showHistory = true">
      &#128196;
    </button>
    <header class="hero">
      <div class="hero-text">
        <p class="eyebrow">{{ t("eyebrow") }}</p>
        <h1>DATAFLOWBI</h1>
        <p class="subtitle">{{ t("subtitle") }}</p>
        <div class="actions">
          <label class="upload-btn">
            <input type="file" accept=".csv,.xlsx" @change="onFileChange" />
            <span>
              {{ selectedFile ? selectedFile.name : t("chooseFile") }}
            </span>
          </label>
          <button
            class="primary-btn"
            :disabled="!selectedFile || isUploading"
            @click="openSelection"
          >
            {{ isUploading ? t("uploading") : t("parseData") }}
          </button>
        </div>
        <div v-if="hasParsed" class="actions actions--secondary">
          <button
            class="primary-btn primary-btn--blue"
            type="button"
            @click="showCleanPanel = true"
          >
            {{ t("cleanTitle") }}
          </button>
        </div>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      </div>

      <PreviewCard
        v-if="showPreviewCard"
        :preview="preview"
        :showAllFields="showAllFields"
        :totalFields="totalFields"
        :visibleFields="visibleFields"
        :hasMoreFields="hasMoreFields"
        @toggleFields="toggleFields"
      />
    </header>

    <ReportSection
      v-if="showReportSection"
      :reportData="activeReport"
      :showSample="showSampleSection"
      :sampleRows="sampleRows"
      :sampleColumns="sampleColumns"
      :statsRows="reportStatsRows"
    />

    <section v-if="showChartSection" class="chart-section">
      <div class="chart-header">
        <h2>{{ t("chartTitle") }}</h2>
        <p>{{ t("chartSubtitle") }}</p>
      </div>
      <div class="chart-panel">
        <ChartToolbar
          :showOptions="showChartOptions"
          :hasCharts="hasCharts"
          :title="currentChartTitle"
          :showFilter="showFilterPanel"
          :comparisonMode="comparisonMode"
          @toggleOptions="toggleChartOptions"
          @toggleFilter="showFilterPanel = !showFilterPanel"
          @toggleComparison="comparisonMode = !comparisonMode; selectedComparisonFields = []"
          @setup="openChartSetup"
          @openExport="showExportPanel = true"
        />
        <ChartOptionsPanel
          :show="showChartOptions && hasCharts"
          :analysisOptions="analysisOptions"
          :category="chartCategory"
          :chartTypeVal="chartType"
          :featureVal="chartFeature"
          :comparison="comparisonMode"
          :selecteds="selectedComparisonFields"
          :histogramFields="histogramFeatures"
          :freqFields="frequencyFields"
          :boxplotCount="boxplotFields.length"
          :corrFieldCount="reportData?.correlation?.fields?.length || 0"
          :groupCatFields="groupCategoricalFields"
          :groupAgg="groupAggregation"
          :binningFields="binningFields"
          :binMethod="binningMethod"
          :violinFields="violinFields"
          :scatterFields="scatterFields"
          :scatterX="scatterXField"
          :scatterY="scatterYField"
          :hmFieldCount="reportData?.missing_heatmap?.fields?.length || 0"
          :hmRowCount="reportData?.missing_heatmap?.rows || 0"
          :tsFields="timeseriesFields"
          :tsPeriod="timeseriesPeriod"
          :outlierFields="outlierFields"
          :outlierIqrCount="reportData?.outliers?.[chartFeature]?.iqr?.count || 0"
          :outlierZscoreCount="reportData?.outliers?.[chartFeature]?.zscore?.count || 0"
          :paretoFields="paretoFields"
          :binCount="histogramBinCount"
          :normalize="histogramNormalize"
          @selectAnalysis="selectAnalysis"
          @update:chartType="chartType = $event"
          @update:feature="chartFeature = $event"
          @toggleComparisonField="toggleComparisonField"
          @update:binCount="histogramBinCount = $event"
          @update:normalize="histogramNormalize = $event"
          @update:groupAgg="groupAggregation = $event"
          @update:binMethod="binningMethod = $event"
          @update:scatterX="scatterXField = $event"
          @update:scatterY="scatterYField = $event"
          @update:tsPeriod="timeseriesPeriod = $event"
        />
        <div ref="chartEl" class="chart-canvas"></div>
        <p v-if="!hasCharts || !hasChartData" class="chart-empty">{{ t("chartEmpty") }}</p>
      </div>
    </section>

    <section v-if="hasParsed" class="ml-section">
      <div class="chart-header">
        <h2>{{ t("mlTitle") }}</h2>
        <p>{{ t("mlSubtitle") }}</p>
      </div>
      <div class="ml-panel">
        <div class="ml-toolbar">
          <button class="primary-btn" type="button" @click="openMLDialog">
            {{ t("mlOpen") }}
          </button>
        </div>
        <div v-if="mlLoading" class="loading">{{ t("loading") }}</div>
        <div v-else-if="mlError" class="error">{{ mlError }}</div>
        <div v-else-if="!mlResult" class="empty-state">{{ t("mlEmpty") }}</div>
        <div v-else class="ml-results">
          <div class="ml-summary">
            <div>{{ t("mlTaskType") }}: {{ mlResult.task_type }}</div>
            <div>{{ t("mlModel") }}: {{ mlResult.model_type }}</div>
            <div>{{ t("mlTarget") }}: {{ mlResult.target }}</div>
            <div>{{ t("mlFeatureCount") }}: {{ mlResult.features?.length || 0 }}</div>
            <div>{{ t("mlTrainSize") }}: {{ mlResult.split?.sizes?.train }}</div>
            <div v-if="mlResult.split?.sizes?.val">{{ t("mlValSize") }}: {{ mlResult.split?.sizes?.val }}</div>
            <div>{{ t("mlTestSize") }}: {{ mlResult.split?.sizes?.test }}</div>
          </div>

          <div class="ml-metrics">
            <div class="selection-label">{{ t("mlMetrics") }}</div>
            <table class="report-table">
              <thead>
                <tr>
                  <th>{{ t("mlSplit") }}</th>
                  <th>{{ t("mlMetricR2") }}</th>
                  <th>{{ t("mlMetricMAE") }}</th>
                  <th>{{ t("mlMetricRMSE") }}</th>
                  <th>{{ t("mlMetricAcc") }}</th>
                  <th>{{ t("mlMetricPrecision") }}</th>
                  <th>{{ t("mlMetricRecall") }}</th>
                  <th>{{ t("mlMetricF1") }}</th>
                  <th>{{ t("mlMetricAUC") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>train</td>
                  <td>{{ formatMetric(mlResult.metrics?.train?.r2) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.train?.mae) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.train?.rmse) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.train?.accuracy) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.train?.precision) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.train?.recall) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.train?.f1) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.train?.roc_auc) }}</td>
                </tr>
                <tr v-if="hasValMetrics">
                  <td>val</td>
                  <td>{{ formatMetric(mlResult.metrics?.val?.r2) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.val?.mae) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.val?.rmse) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.val?.accuracy) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.val?.precision) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.val?.recall) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.val?.f1) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.val?.roc_auc) }}</td>
                </tr>
                <tr>
                  <td>test</td>
                  <td>{{ formatMetric(mlResult.metrics?.test?.r2) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.test?.mae) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.test?.rmse) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.test?.accuracy) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.test?.precision) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.test?.recall) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.test?.f1) }}</td>
                  <td>{{ formatMetric(mlResult.metrics?.test?.roc_auc) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="mlResult.ols" class="ml-ols">
            <div class="selection-label">{{ t("mlOlsTitle") }}</div>
            <div class="ml-ols-summary">
              <span>R2: {{ formatMetric(mlResult.ols.summary?.r2) }}</span>
              <span>Adj R2: {{ formatMetric(mlResult.ols.summary?.adj_r2) }}</span>
              <span>AIC: {{ formatMetric(mlResult.ols.summary?.aic) }}</span>
              <span>BIC: {{ formatMetric(mlResult.ols.summary?.bic) }}</span>
              <span>N: {{ mlResult.ols.summary?.nobs }}</span>
            </div>
            <div class="report-table-wrapper">
              <table class="report-table">
                <thead>
                  <tr>
                    <th>{{ t("mlFeature") }}</th>
                    <th>Coef.</th>
                    <th>Std.Err.</th>
                    <th>t</th>
                    <th>P>|t|</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in mlResult.ols.table" :key="row.feature">
                    <td>{{ row.feature }}</td>
                    <td>{{ formatMetric(row['Coef.']) }}</td>
                    <td>{{ formatMetric(row['Std.Err.']) }}</td>
                    <td>{{ formatMetric(row['t']) }}</td>
                    <td>{{ formatMetric(row['P>|t|']) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-else class="ml-coef">
            <div class="selection-label">{{ t("mlCoeffTitle") }}</div>
            <div class="report-table-wrapper">
              <table class="report-table">
                <thead>
                  <tr>
                    <th>{{ t("mlFeature") }}</th>
                    <th>{{ t("mlCoefficient") }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in mlResult.coefficients || []" :key="row.feature + (row.class ?? '')">
                    <td>{{ row.feature }}</td>
                    <td>{{ formatMetric(row.coef) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>

    <SelectionDialog
      :show="showSelection"
      :selection="selection"
      :selectionMode="selectionMode"
      :disabled="isUploading"
      @close="closeSelection"
      @confirm="confirmSelection"
      @update:selection="selection = $event"
    />
    <ChartSetupDialog
      :show="showChartSetup"
      :chartTypes="tempChartTypes"
      :selectionMode="selectionMode"
      @close="closeChartSetup"
      @confirm="confirmChartSetup"
      @update:chartTypes="tempChartTypes = $event"
    />
    <FilterPanel
      :showFilterPanel="showFilterPanel"
      :filterInfo="preview?.filter_info"
      :ranges="filterNumericRanges"
      :allFields="preview?.fields || []"
      :selectedFields="selectedFields"
      :selectionMode="selectionMode"
      @update:ranges="filterNumericRanges = $event"
      @update:selectedFields="selectedFields = $event"
      @apply="applyFilter"
      @reset="resetFilter"
      @close="showFilterPanel = false"
    />
    <ExportDialog
      :show="showExportPanel"
      :selectionMode="selectionMode"
      @close="showExportPanel = false"
      @download="downloadChart"
      @exportDocx="handleExportDocx"
      @exportPdf="handleExportPdf"
      @exportExcel="handleExportExcel"
      @exportPptx="handleExportPptx"
    />
    <CleanPanel
      :show="showCleanPanel"
      :fields="preview?.fields || []"
      :filterInfo="preview?.filter_info"
      :quality="preview?.report?.quality"
      :savedName="savedName"
      :selectionMode="selectionMode"
      @close="showCleanPanel = false"
      @cleaned="onCleaned"
    />
    <HistoryPanel
      :show="showHistory"
      :selectionMode="selectionMode"
      @close="showHistory = false"
      @select="onHistorySelect"
    />
    <MachineLearningDialog
      :show="showMLDialog"
      :selectionMode="selectionMode"
      :fields="preview?.fields || []"
      :filterInfo="preview?.filter_info"
      @close="showMLDialog = false"
      @train="runMLTrain"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "./composables/useI18n";
import { useFileUpload } from "./composables/useFileUpload";
import { useSelection } from "./composables/useSelection";
import { useChart } from "./composables/useChart";
import { exportReportDocx, exportReportExcel, exportReportPdf, exportReportPptx } from "./api/upload";
import { trainModel } from "./api/ml";
import SettingsMenu from "./components/SettingsMenu.vue";
import PreviewCard from "./components/PreviewCard.vue";
import ReportSection from "./components/ReportSection.vue";
import SelectionDialog from "./components/SelectionDialog.vue";
import ChartSetupDialog from "./components/ChartSetupDialog.vue";
import FilterPanel from "./components/FilterPanel.vue";
import ChartToolbar from "./components/ChartToolbar.vue";
import ChartOptionsPanel from "./components/ChartOptionsPanel.vue";
import HistoryPanel from "./components/HistoryPanel.vue";
import CleanPanel from "./components/CleanPanel.vue";
import ExportDialog from "./components/ExportDialog.vue";
import MachineLearningDialog from "./components/MachineLearningDialog.vue";

const { locale, t, setLanguage } = useI18n();
const showSettingsMenu = ref(false);
const showHistory = ref(false);
const selectionMode = ref("dialog");

const {
  selectedFile, preview, isUploading, errorMessage, showAllFields, savedName,
  filteredData, filterNumericRanges, showFilterPanel, hasParsed, selectedFields,
  reportData, sampleRows, totalFields, visibleFields, hasMoreFields,
  sampleColumns, reportStatsRows, activeReport,
  onFileChange, runUpload, applyFilter, resetFilter, toggleFields, loadHistoryRecord,
} = useFileUpload();

let _syncChartSelection = null;

const {
  selection, appliedSelection, chartConfigApplied, showChartSetup,
  tempChartTypes, appliedChartTypes, showSelection,
  hasSelectedCharts, showPreviewCard, showReportSection, showSampleSection,
  showChartSection, analysisOptions,
  openSelection, closeSelection,
  openChartSetup, closeChartSetup,
} = useSelection({ runUpload, hasParsedRef: hasParsed, isUploadingRef: isUploading });

const {
  chartCategory, chartType, chartFeature, chartEl, chartInstance,
  histogramBinCount, histogramNormalize, rebinData, groupAggregation, binningMethod,
  scatterXField, scatterYField, timeseriesPeriod, comparisonMode, selectedComparisonFields,
  histogramFeatures, frequencyFields, paretoFields, boxplotFields, groupCategoricalFields,
  binningFields, violinFields, scatterFields, timeseriesFields, outlierFields,
  chartOption, hasChartData, currentChartTitle,
  renderChart, resizeChart, syncChartSelection, selectAnalysis, selectChartType,
  selectFeature, toggleComparisonField, rebin, downloadChart, resetChart,
} = useChart({ activeReport, savedName, analysisOptions });

_syncChartSelection = syncChartSelection;

const showChartOptions = ref(true);
const showCleanPanel = ref(false);
const showExportPanel = ref(false);
const showMLDialog = ref(false);
const mlLoading = ref(false);
const mlError = ref("");
const mlResult = ref(null);

const hasCharts = computed(
  () => showChartSection.value && analysisOptions.value.length > 0
);

const onHistorySelect = async (record) => {
  showHistory.value = false;
  try {
    await loadHistoryRecord(record.id);
    showSelection.value = false;
    appliedSelection.value = {
      preview: true,
      report: true,
      sample: true,
      charts_enabled: true,
    };
    hasParsed.value = true;
    if (!chartConfigApplied.value) {
      chartConfigApplied.value = true;
      _syncChartSelection();
    }
  } catch {
    // error already set by loadHistoryRecord
  }
};

const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

const buildChartPayload = () => {
  if (!chartInstance.value || !hasChartData.value) return [];
  const dataUrl = chartInstance.value.getDataURL({
    type: "png",
    pixelRatio: 2,
    backgroundColor: "#fff",
  });
  return [{ title: currentChartTitle.value || "Chart", data_url: dataUrl }];
};

const handleExportDocx = async () => {
  if (!savedName.value) return;
  try {
    const blob = await exportReportDocx(
      savedName.value,
      preview.value?.filename || "report",
      buildChartPayload()
    );
    downloadBlob(blob, `${preview.value?.filename || "report"}.docx`);
  } catch (e) {
    console.error("Word export failed:", e);
    errorMessage.value = e?.response?.data?.detail || "Word export failed";
  }
};

const handleExportExcel = async () => {
  if (!savedName.value) return;
  try {
    const blob = await exportReportExcel(savedName.value, preview.value?.filename || "report");
    downloadBlob(blob, `${preview.value?.filename || "report"}.xlsx`);
  } catch (e) {
    console.error("Excel export failed:", e);
    errorMessage.value = e?.response?.data?.detail || "Excel export failed";
  }
};

const onCleaned = (result) => {
  preview.value = { ...preview.value, ...result };
  if (result?.saved_name) {
    savedName.value = result.saved_name;
  }
  showCleanPanel.value = false;
};

const handleExportPdf = async () => {
  if (!savedName.value) return;
  try {
    const blob = await exportReportPdf(
      savedName.value,
      preview.value?.filename || "report",
      buildChartPayload()
    );
    downloadBlob(blob, `${preview.value?.filename || "report"}.pdf`);
  } catch (e) {
    console.error("PDF export failed:", e);
    errorMessage.value = e?.response?.data?.detail || "PDF export failed";
  }
};

const handleExportPptx = async () => {
  if (!savedName.value) return;
  try {
    const blob = await exportReportPptx(
      savedName.value,
      preview.value?.filename || "report",
      buildChartPayload()
    );
    downloadBlob(blob, `${preview.value?.filename || "report"}.pptx`);
  } catch (e) {
    console.error("PPT export failed:", e);
    errorMessage.value = e?.response?.data?.detail || "PPT export failed";
  }
};

const toggleChartOptions = () => {
  if (!hasCharts.value) return;
  showChartOptions.value = !showChartOptions.value;
};

const openMLDialog = () => {
  if (!hasParsed.value) return;
  showMLDialog.value = true;
};

const runMLTrain = async (config) => {
  if (!savedName.value) return;
  mlLoading.value = true;
  mlError.value = "";
  try {
    const result = await trainModel({
      saved_name: savedName.value,
      ...config,
    });
    mlResult.value = result;
  } catch (e) {
    mlError.value = e?.response?.data?.detail || "ML training failed";
  } finally {
    mlLoading.value = false;
    showMLDialog.value = false;
  }
};

const formatMetric = (value) => {
  if (value === null || value === undefined) return "-";
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  return n.toFixed(4);
};

const hasValMetrics = computed(() => Boolean(mlResult.value?.metrics?.val));

const confirmSelection = async () => {
  const normalized = {
    preview: Boolean(selection.value.preview),
    report: Boolean(selection.value.report),
    sample: Boolean(selection.value.sample) && Boolean(selection.value.report),
    charts_enabled: Boolean(selection.value.charts_enabled),
  };
  if (!normalized.report) normalized.sample = false;
  appliedSelection.value = normalized;
  showSelection.value = false;
  showChartOptions.value = false;
  await runUpload();
  if (normalized.charts_enabled && !chartConfigApplied.value) {
    chartConfigApplied.value = true;
    _syncChartSelection();
  }
};

const confirmChartSetup = () => {
  appliedChartTypes.value = { ...tempChartTypes.value };
  chartConfigApplied.value = true;
  showChartSetup.value = false;
  showChartOptions.value = false;
  _syncChartSelection();
};

watch(activeReport, () => {
  syncChartSelection();
  nextTick(renderChart);
});

watch(
  () => selection.value.report,
  (value) => { if (!value) selection.value.sample = false; }
);

watch([chartCategory, chartType, chartFeature], () => {
  nextTick(renderChart);
});

watch([histogramBinCount, histogramNormalize], () => {
  if (chartCategory.value === "feature_distribution") rebin();
});

watch(rebinData, () => { nextTick(renderChart); });

watch(analysisOptions, () => { syncChartSelection(); });

watch(locale, () => { nextTick(renderChart); });

watch(showChartSection, (value) => {
  if (!value && chartInstance.value) {
    chartInstance.value.dispose();
    chartInstance.value = null;
  }
  if (!value) showChartOptions.value = false;
  nextTick(renderChart);
});

watch(savedName, () => {
  mlResult.value = null;
  mlError.value = "";
});

onMounted(() => {
  window.addEventListener("resize", resizeChart);
  nextTick(renderChart);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeChart);
  if (chartInstance.value) {
    chartInstance.value.dispose();
    chartInstance.value = null;
  }
});
</script>
