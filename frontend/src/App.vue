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
          @download="downloadChart"
          @setup="openChartSetup"
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
      @update:ranges="filterNumericRanges = $event"
      @update:selectedFields="selectedFields = $event"
      @apply="applyFilter"
      @reset="resetFilter"
      @close="showFilterPanel = false"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "./composables/useI18n";
import { useFileUpload } from "./composables/useFileUpload";
import { useSelection } from "./composables/useSelection";
import { useChart } from "./composables/useChart";
import SettingsMenu from "./components/SettingsMenu.vue";
import PreviewCard from "./components/PreviewCard.vue";
import ReportSection from "./components/ReportSection.vue";
import SelectionDialog from "./components/SelectionDialog.vue";
import ChartSetupDialog from "./components/ChartSetupDialog.vue";
import FilterPanel from "./components/FilterPanel.vue";
import ChartToolbar from "./components/ChartToolbar.vue";
import ChartOptionsPanel from "./components/ChartOptionsPanel.vue";

const { locale, t, setLanguage } = useI18n();
const showSettingsMenu = ref(false);
const selectionMode = ref("dialog");

const {
  selectedFile, preview, isUploading, errorMessage, showAllFields, savedName,
  filteredData, filterNumericRanges, showFilterPanel, hasParsed, selectedFields,
  reportData, sampleRows, totalFields, visibleFields, hasMoreFields,
  sampleColumns, reportStatsRows, activeReport,
  onFileChange, runUpload, applyFilter, resetFilter, toggleFields,
} = useFileUpload();

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

const showChartOptions = ref(true);

const hasCharts = computed(
  () => showChartSection.value && analysisOptions.value.length > 0
);

const toggleChartOptions = () => {
  if (!hasCharts.value) return;
  showChartOptions.value = !showChartOptions.value;
};

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
    syncChartSelection();
  }
};

const confirmChartSetup = () => {
  appliedChartTypes.value = { ...tempChartTypes.value };
  chartConfigApplied.value = true;
  showChartSetup.value = false;
  showChartOptions.value = false;
  syncChartSelection();
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
