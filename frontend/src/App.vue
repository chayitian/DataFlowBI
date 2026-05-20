<template>
  <div class="page">
    <!-- 全局设置：语言和弹窗/抽屉展示模式。 -->
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
    <!-- 首页上传区。解析完成后，这里也会展示清洗和特征工程入口。 -->
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
          <button
            class="primary-btn primary-btn--blue"
            type="button"
            @click="showFeatureEngineeringPanel = true"
          >
            {{ t("featureEngineeringTitle") }}
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

    <!-- 后端 report_builder.py 生成的静态数据画像表。 -->
    <ReportSection
      v-if="showReportSection"
      :reportData="activeReport"
      :showSample="showSampleSection"
      :sampleRows="sampleRows"
      :sampleColumns="sampleColumns"
      :statsRows="reportStatsRows"
    />

    <!-- 交互式图表面板；useChart.js 管理图表状态和 ECharts 渲染。 -->
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

    <!-- /ml/train 返回后展示机器学习结果。 -->
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
        <MLResults :loading="mlLoading" :error="mlError" :result="mlResult" />
      </div>
    </section>

    <!-- 下面的弹窗/抽屉组件由 script 部分的 refs 控制。 -->
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
    <FeatureEngineeringDialog
      :show="showFeatureEngineeringPanel"
      :fields="preview?.fields || []"
      :filterInfo="preview?.filter_info"
      :savedName="savedName"
      :selectionMode="selectionMode"
      @close="showFeatureEngineeringPanel = false"
      @engineered="onFeatureEngineered"
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
      :originalFields="originalFeatureFields"
      :engineeredFields="engineeredFeatureFields"
      :filterInfo="preview?.filter_info"
      @close="showMLDialog = false"
      @train="runMLTrain"
    />
  </div>
</template>

<script setup>
// App.vue 负责组装整个页面。可复用状态放在 composables 中，本文件负责协调跨功能动作，
// 例如上传 -> 图表重置、清洗/特征工程 -> 预览刷新、ML 训练 -> 结果展示。
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "./composables/useI18n";
import { useFileUpload } from "./composables/useFileUpload";
import { useSelection } from "./composables/useSelection";
import { useChart } from "./composables/useChart";
import { useExport } from "./composables/useExport";
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
import FeatureEngineeringDialog from "./components/FeatureEngineeringDialog.vue";
import MachineLearningDialog from "./components/MachineLearningDialog.vue";
import MLResults from "./components/MLResults.vue";

const { locale, t, setLanguage } = useI18n();
const showSettingsMenu = ref(false);
const showHistory = ref(false);
const selectionMode = ref("dialog");

// 上传、预览和筛选的状态与动作。savedName 是后端缓存键，筛选、清洗、导出、
// 特征工程和 ML 接口都会使用它。
const {
  selectedFile, preview, isUploading, errorMessage, showAllFields, savedName,
  filteredData, filterNumericRanges, showFilterPanel, hasParsed, selectedFields,
  reportData, sampleRows, totalFields, visibleFields, hasMoreFields,
  sampleColumns, reportStatsRows, activeReport,
  onFileChange, runUpload, applyFilter, resetFilter, toggleFields, loadHistoryRecord,
} = useFileUpload();

let _syncChartSelection = null;

// 控制解析后用户要展示哪些分区，以及当前报告启用哪些图表类别。
const {
  selection, appliedSelection, chartConfigApplied, showChartSetup,
  tempChartTypes, appliedChartTypes, showSelection,
  hasSelectedCharts, showPreviewCard, showReportSection, showSampleSection,
  showChartSection, analysisOptions,
  openSelection, closeSelection,
  openChartSetup, closeChartSetup,
} = useSelection({ runUpload, hasParsedRef: hasParsed, isUploadingRef: isUploading });

// 图表状态有意从 App.vue 中拆出，因为 ECharts 选项和报告相关默认值是前端最密集的逻辑。
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

const {
  handleExportDocx,
  handleExportExcel,
  handleExportPdf,
  handleExportPptx,
} = useExport({ savedName, preview, chartInstance, hasChartData, currentChartTitle, errorMessage });

const showChartOptions = ref(true);
const showCleanPanel = ref(false);
const showFeatureEngineeringPanel = ref(false);
const showExportPanel = ref(false);
const showMLDialog = ref(false);
const mlLoading = ref(false);
const mlError = ref("");
const mlResult = ref(null);
const originalFields = ref([]);
const engineeredFields = ref([]);

const hasCharts = computed(
  () => showChartSection.value && analysisOptions.value.length > 0
);

const currentFields = computed(() => preview.value?.fields || []);
// 这些列表让 ML 弹窗可以分开展示原始特征和生成特征。
const originalFeatureFields = computed(() => originalFields.value.filter((field) => currentFields.value.includes(field)));
const engineeredFeatureFields = computed(() => engineeredFields.value.filter((field) => currentFields.value.includes(field)));

const uniqueFields = (fields) => Array.from(new Set(fields));

const onHistorySelect = async (record) => {
  // 加载历史记录会从磁盘缓存快照恢复预览状态。
  showHistory.value = false;
  try {
    await loadHistoryRecord(record.id);
    originalFields.value = preview.value?.fields || [];
    engineeredFields.value = [];
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
    // 错误信息已由 loadHistoryRecord 设置。
  }
};

const onCleaned = (result) => {
  // 清洗会返回新的 saved_name。更新 preview 后，后续动作会使用清洗后的快照，
  // 而不是原始上传文件。
  preview.value = { ...preview.value, ...result };
  if (result?.saved_name) {
    savedName.value = result.saved_name;
  }
  const fields = result?.fields || [];
  originalFields.value = originalFields.value.filter((field) => fields.includes(field));
  engineeredFields.value = engineeredFields.value.filter((field) => fields.includes(field));
  showCleanPanel.value = false;
};

const onFeatureEngineered = (result) => {
  // 单独记录生成列，让 ML 可以清晰展示特征分组。
  const createdFields = result?.engineered_fields
    || (result?.feature_engineering_log || []).flatMap((log) => log.created_fields || []);
  if (!originalFields.value.length) {
    originalFields.value = preview.value?.fields || [];
  }
  preview.value = { ...preview.value, ...result };
  if (result?.saved_name) {
    savedName.value = result.saved_name;
  }
  const fields = result?.fields || [];
  originalFields.value = originalFields.value.filter((field) => fields.includes(field));
  engineeredFields.value = uniqueFields([...engineeredFields.value, ...createdFields])
    .filter((field) => fields.includes(field));
  showFeatureEngineeringPanel.value = false;
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
  // 弹窗发出模型配置；这里补上 saved_name 并调用 API。
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

const confirmSelection = async () => {
  // 用户确认要展示的分区后才开始上传。
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
  if (preview.value?.fields) {
    originalFields.value = preview.value.fields;
    engineeredFields.value = [];
  }
  if (normalized.charts_enabled && !chartConfigApplied.value) {
    chartConfigApplied.value = true;
    _syncChartSelection();
  }
};

const confirmChartSetup = () => {
  // 应用图表类别选择，并让 useChart 选择有效默认值。
  appliedChartTypes.value = { ...tempChartTypes.value };
  chartConfigApplied.value = true;
  showChartSetup.value = false;
  showChartOptions.value = false;
  _syncChartSelection();
};

watch(activeReport, () => {
  // 报告变化可能让图表字段失效，因此渲染前先同步选择。
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
  // 图表分区隐藏时销毁 ECharts 实例，释放 canvas 内存。
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
