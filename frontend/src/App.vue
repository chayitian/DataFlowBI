<template>
  <div class="page">
    <div class="top-actions">
      <div class="lang-menu">
        <button class="lang-button" type="button" @click="toggleSettingsMenu">
          {{ t("settings") }}
        </button>
        <div v-if="showSettingsMenu" class="lang-dropdown">
          <div class="lang-title">{{ t("language") }}</div>
          <button
            :class="['lang-option', { active: locale === 'zh' }]"
            type="button"
            @click="setLanguage('zh')"
          >
            {{ t("langChinese") }}
          </button>
          <button
            :class="['lang-option', { active: locale === 'en' }]"
            type="button"
            @click="setLanguage('en')"
          >
            {{ t("langEnglish") }}
          </button>
          <div class="settings-divider"></div>
          <div class="lang-title">{{ t("selectionModeTitle") }}</div>
          <button
            :class="['lang-option', { active: selectionMode === 'dialog' }]"
            type="button"
            @click="setSelectionMode('dialog')"
          >
            {{ t("selectionModeDialog") }}
          </button>
          <button
            :class="['lang-option', { active: selectionMode === 'drawer' }]"
            type="button"
            @click="setSelectionMode('drawer')"
          >
            {{ t("selectionModeDrawer") }}
          </button>
        </div>
      </div>
    </div>
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

      <div v-if="showPreviewCard" class="hero-card">
        <div class="card-title">{{ t("previewSummary") }}</div>
        <div v-if="preview" class="preview-grid">
          <div class="preview-item">
            <span>{{ t("filename") }}</span>
            <strong>{{ preview.filename }}</strong>
          </div>
          <div class="preview-item">
            <span>{{ t("rows") }}</span>
            <strong>{{ preview.rows }}</strong>
          </div>
          <div class="preview-item">
            <span>{{ t("columns") }}</span>
            <strong>{{ preview.columns }}</strong>
          </div>
        </div>
        <div v-else class="empty-state">{{ t("emptyState") }}</div>
        <div v-if="preview" class="fields">
          <span
            v-for="field in visibleFields"
            :key="field"
            class="field-chip"
          >
            {{ field }}
          </span>
        </div>
        <div v-if="preview && hasMoreFields" class="fields-controls">
          <button class="fields-toggle" type="button" @click="toggleFields">
            {{ showAllFields ? t("collapseFields") : t("expandFields") }}
          </button>
          <span class="fields-count">
            {{ visibleFields.length }} / {{ totalFields }} {{ t("fieldsUnit") }}
          </span>
        </div>
      </div>
    </header>

    <section v-if="showReportSection" class="report-section">
      <div class="report-header">
        <h2>{{ t("reportTitle") }}</h2>
        <p>{{ t("reportSubtitle") }}</p>
      </div>
      <div v-if="reportData" class="report-grid">
        <div class="report-card report-card--tall">
          <div class="card-title">{{ t("reportStatsTitle") }}</div>
          <div class="report-body">
            <div v-if="reportStatsRows.length" class="report-table-wrapper">
              <table class="report-table">
                <thead>
                  <tr>
                    <th>{{ t("fieldLabel") }}</th>
                    <th>{{ t("typeLabel") }}</th>
                    <th>{{ t("missingLabel") }}</th>
                    <th>{{ t("missingRateLabel") }}</th>
                    <th>{{ t("countLabel") }}</th>
                    <th>{{ t("meanLabel") }}</th>
                    <th>{{ t("stdLabel") }}</th>
                    <th>{{ t("minLabel") }}</th>
                    <th>{{ t("maxLabel") }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in reportStatsRows" :key="row.field">
                    <td>{{ row.field }}</td>
                    <td>{{ row.dtype }}</td>
                    <td>{{ row.missing }}</td>
                    <td>{{ formatPercent(row.missingRate) }}</td>
                    <td>{{ formatNumber(row.count) }}</td>
                    <td>{{ formatNumber(row.mean) }}</td>
                    <td>{{ formatNumber(row.std) }}</td>
                    <td>{{ formatNumber(row.min) }}</td>
                    <td>{{ formatNumber(row.max) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-else class="empty-state">{{ t("reportStatsEmpty") }}</p>
          </div>
        </div>

        <div v-if="showSampleSection" class="report-card report-card--full">
          <div class="card-title">{{ t("sampleTitle") }}</div>
          <div class="report-body">
            <div v-if="sampleRows.length" class="report-table-wrapper">
              <table class="report-table">
                <thead>
                  <tr>
                    <th v-for="column in sampleColumns" :key="column">
                      {{ column }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in sampleRows" :key="index">
                    <td v-for="column in sampleColumns" :key="column">
                      {{ formatValue(row[column]) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-else class="empty-state">{{ t("sampleEmpty") }}</p>
          </div>
        </div>
      </div>
      <p v-else class="empty-state">{{ t("reportEmpty") }}</p>
    </section>

    <section v-if="showChartSection" class="chart-section">
      <div class="chart-header">
        <h2>{{ t("chartTitle") }}</h2>
        <p>{{ t("chartSubtitle") }}</p>
      </div>
      <div class="chart-panel">
        <div class="chart-toolbar">
          <button
            class="chart-picker-toggle"
            type="button"
            :disabled="!hasCharts"
            @click="toggleChartPicker"
          >
            {{ showChartPicker ? t("collapseCharts") : t("expandCharts") }}
          </button>
          <div class="chart-current">
            <span>{{ currentChartTitle }}</span>
          </div>
        </div>
        <div v-if="showChartPicker && hasCharts" class="chart-picker">
          <button
            v-for="(slide, index) in chartSlides"
            :key="slide.title"
            :class="['chart-picker-item', { active: index === chartIndex }]"
            type="button"
            @click="selectChart(index)"
          >
            {{ slide.title }}
          </button>
        </div>
        <div ref="chartEl" class="chart-canvas"></div>
        <p v-if="!hasCharts" class="chart-empty">{{ t("chartEmpty") }}</p>
      </div>
    </section>

    <div
      v-if="showSelection"
      class="selection-overlay"
      @click.self="closeSelection"
    >
      <div
        :class="[
          'selection-panel',
          selectionMode === 'drawer' ? 'is-drawer' : 'is-dialog',
        ]"
      >
        <div class="selection-header">
          <h3>{{ t("selectionTitle") }}</h3>
          <button class="icon-button" type="button" @click="closeSelection">
            ×
          </button>
        </div>
        <div class="selection-body">
          <div class="selection-group">
            <div class="selection-label">{{ t("selectionBasics") }}</div>
            <label class="checkbox">
              <input type="checkbox" v-model="selection.preview" />
              <span>{{ t("selectionPreview") }}</span>
            </label>
            <label class="checkbox">
              <input type="checkbox" v-model="selection.report" />
              <span>{{ t("selectionReport") }}</span>
            </label>
            <label class="checkbox" :class="{ disabled: !selection.report }">
              <input
                type="checkbox"
                v-model="selection.sample"
                :disabled="!selection.report"
              />
              <span>{{ t("selectionSample") }}</span>
            </label>
          </div>

          <div class="selection-group">
            <div class="selection-label">{{ t("selectionCharts") }}</div>
            <p class="selection-hint">{{ t("selectionChartsHint") }}</p>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.missing_rate"
              />
              <span>{{ t("analysisMissingRate") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.histogram_distribution"
              />
              <span>{{ t("analysisHistogram") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.numeric_mean"
              />
              <span>{{ t("analysisNumericMean") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.numeric_max"
              />
              <span>{{ t("analysisNumericMax") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.numeric_min"
              />
              <span>{{ t("analysisNumericMin") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.dtype_distribution"
              />
              <span>{{ t("analysisTypeDistribution") }}</span>
            </label>
          </div>
        </div>
        <div class="selection-footer">
          <button class="ghost-button" type="button" @click="closeSelection">
            {{ t("cancel") }}
          </button>
          <button
            class="primary-btn"
            type="button"
            :disabled="isUploading"
            @click="confirmSelection"
          >
            {{ t("confirm") }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import { uploadDataset } from "./api/upload";

const locale = ref("zh");
const showSettingsMenu = ref(false);
const selectionMode = ref("dialog");
const showSelection = ref(false);
const hasParsed = ref(false);

const buildDefaultSelection = () => ({
  preview: true,
  report: true,
  sample: false,
  charts: {
    missing_rate: true,
    histogram_distribution: true,
    numeric_mean: false,
    numeric_max: false,
    numeric_min: false,
    dtype_distribution: true,
  },
});

const selection = ref(buildDefaultSelection());
const appliedSelection = ref(buildDefaultSelection());

const messages = {
  zh: {
    settings: "设置",
    language: "语言",
    selectionModeTitle: "弹窗样式",
    selectionModeDialog: "对话框",
    selectionModeDrawer: "侧边抽屉",
    langChinese: "中文",
    langEnglish: "English",
    eyebrow: "数据分析",
    subtitle: "上传 CSV 或 XLSX 文件，预览行数、列数与字段列表。",
    chooseFile: "选择文件",
    uploading: "上传中...",
    parseData: "开始解析",
    previewSummary: "预览摘要",
    filename: "文件名",
    rows: "行数",
    columns: "列数",
    emptyState: "上传文件后可查看行数、列数与字段。",
    chartTitle: "统计分析与可视化",
    chartSubtitle: "展开可视化选项并选择要展示的图表。",
    chartEmpty: "暂无可视化数据，请先上传文件。",
    analysisMethod: "分析方法",
    analysisMissingRate: "缺失率",
    analysisNumericMean: "均值",
    analysisNumericMax: "最大值",
    analysisNumericMin: "最小值",
    analysisTypeDistribution: "字段类型分布",
    analysisHistogram: "直方图 + 分布",
    chartTypeBar: "柱状图",
    chartTypeLine: "折线图",
    chartTypePie: "饼图",
    uploadError: "上传失败，请检查服务是否启动。",
    reportTitle: "分析报告",
    reportSubtitle: "包含缺失统计、数值指标与样例数据。",
    reportEmpty: "上传文件后生成分析报告。",
    reportStatsTitle: "缺失与数值统计",
    missingTitle: "缺失值统计",
    missingEmpty: "当前无可用字段。",
    numericTitle: "数值字段统计",
    numericEmpty: "暂无数值字段。",
    sampleTitle: "样例数据",
    sampleEmpty: "暂无样例数据。",
    selectionTitle: "选择展示内容",
    selectionBasics: "基础结果",
    selectionPreview: "预览摘要",
    selectionReport: "分析报告",
    selectionSample: "样例数据",
    reportStatsEmpty: "暂无可用统计数据。",
    expandCharts: "展开可视化选项",
    collapseCharts: "收起可视化选项",
    selectionCharts: "统计分析与可视化",
    selectionChartsHint: "勾选需要展示的图表类型",
    confirm: "开始解析",
    cancel: "取消",
    fieldLabel: "字段",
    typeLabel: "类型",
    missingLabel: "缺失数",
    missingRateLabel: "缺失率",
    countLabel: "数量",
    meanLabel: "均值",
    stdLabel: "标准差",
    minLabel: "最小值",
    maxLabel: "最大值",
    expandFields: "展开全部",
    collapseFields: "收起",
    fieldsUnit: "字段",
  },
  en: {
    settings: "Settings",
    language: "Language",
    selectionModeTitle: "Selection style",
    selectionModeDialog: "Dialog",
    selectionModeDrawer: "Drawer",
    langChinese: "中文",
    langEnglish: "English",
    eyebrow: "Enterprise Data Analytics",
    subtitle: "Upload a CSV or XLSX file to preview rows, columns, and fields.",
    chooseFile: "Choose file",
    uploading: "Uploading...",
    parseData: "Parse data",
    previewSummary: "Preview Summary",
    filename: "Filename",
    rows: "Rows",
    columns: "Columns",
    emptyState: "Upload a file to see rows, columns, and fields.",
    chartTitle: "Analytics & Visualization",
    chartSubtitle: "Expand the chart list and select the visualization to show.",
    chartEmpty: "No chart data available. Please upload a file.",
    analysisMethod: "Analysis method",
    analysisMissingRate: "Missing rate",
    analysisNumericMean: "Mean",
    analysisNumericMax: "Max",
    analysisNumericMin: "Min",
    analysisTypeDistribution: "Type distribution",
    analysisHistogram: "Histogram + Distribution",
    chartTypeBar: "Bar",
    chartTypeLine: "Line",
    chartTypePie: "Pie",
    uploadError: "Upload failed. Please check the server and try again.",
    reportTitle: "Analysis Report",
    reportSubtitle: "Missing stats, numeric metrics, and sample rows.",
    reportEmpty: "Upload a file to generate the analysis report.",
    reportStatsTitle: "Missing + Numeric Stats",
    missingTitle: "Missing Values",
    missingEmpty: "No fields available.",
    numericTitle: "Numeric Summary",
    numericEmpty: "No numeric fields found.",
    sampleTitle: "Sample Rows",
    sampleEmpty: "No sample rows available.",
    selectionTitle: "Choose outputs",
    selectionBasics: "Base results",
    selectionPreview: "Preview summary",
    selectionReport: "Analysis report",
    selectionSample: "Sample rows",
    reportStatsEmpty: "No statistics available.",
    expandCharts: "Expand chart options",
    collapseCharts: "Collapse chart options",
    selectionCharts: "Analytics & visualization",
    selectionChartsHint: "Select chart types to display",
    confirm: "Run analysis",
    cancel: "Cancel",
    fieldLabel: "Field",
    typeLabel: "Type",
    missingLabel: "Missing",
    missingRateLabel: "Missing rate",
    countLabel: "Count",
    meanLabel: "Mean",
    stdLabel: "Std",
    minLabel: "Min",
    maxLabel: "Max",
    expandFields: "Show all",
    collapseFields: "Collapse",
    fieldsUnit: "fields",
  },
};

const selectedFile = ref(null);
const preview = ref(null);
const isUploading = ref(false);
const errorMessage = ref("");
const fieldLimit = 5;
const showAllFields = ref(false);

const reportData = computed(() => preview.value?.report || null);
const numericSummary = computed(() => reportData.value?.numeric_summary || {});
const sampleRows = computed(() => reportData.value?.sample_rows || []);
const totalFields = computed(() => preview.value?.fields?.length ?? 0);
const visibleFields = computed(() => {
  const fields = preview.value?.fields || [];

  return showAllFields.value ? fields : fields.slice(0, fieldLimit);
});
const hasMoreFields = computed(() => totalFields.value > fieldLimit);
const sampleColumns = computed(() => {
  if (!sampleRows.value.length) {
    return [];
  }

  return Object.keys(sampleRows.value[0]);
});
const reportStatsRows = computed(() => {
  if (!reportData.value) {
    return [];
  }

  const dtypes = reportData.value.dtypes || {};
  const missing = reportData.value.missing || {};
  const missingRate = reportData.value.missing_rate || {};
  const summary = reportData.value.numeric_summary || {};

  return Object.keys(dtypes).map((field) => ({
    field,
    dtype: dtypes[field],
    missing: missing[field] ?? 0,
    missingRate: missingRate[field] ?? 0,
    count: summary[field]?.count ?? null,
    mean: summary[field]?.mean ?? null,
    std: summary[field]?.std ?? null,
    min: summary[field]?.min ?? null,
    max: summary[field]?.max ?? null,
  }));
});

const chartIndex = ref(0);
const chartEl = ref(null);
const chartInstance = ref(null);
const showChartPicker = ref(false);

const t = (key) => messages[locale.value]?.[key] ?? key;
const hasSelectedCharts = computed(() => {
  const charts = appliedSelection.value?.charts || {};

  return Object.values(charts).some(Boolean);
});

const showPreviewCard = computed(
  () => hasParsed.value && appliedSelection.value?.preview
);
const showReportSection = computed(
  () => hasParsed.value && appliedSelection.value?.report
);
const showSampleSection = computed(
  () => showReportSection.value && appliedSelection.value?.sample
);
const showChartSection = computed(
  () => hasParsed.value && hasSelectedCharts.value
);

const chartSlides = computed(() => {
  if (!showChartSection.value) {
    return [];
  }

  return buildChartSlides(reportData.value, appliedSelection.value?.charts);
});
const hasCharts = computed(() => chartSlides.value.length > 0);
const currentChartTitle = computed(() => {
  if (!hasCharts.value) {
    return t("chartEmpty");
  }

  return chartSlides.value[chartIndex.value]?.title || "";
});

const formatPercent = (value) => {
  if (value === null || value === undefined) {
    return "-";
  }

  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return "-";
  }

  return `${(numericValue * 100).toFixed(1)}%`;
};

const formatNumber = (value) => {
  if (value === null || value === undefined) {
    return "-";
  }

  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return String(value);
  }

  return Number.isInteger(numericValue)
    ? numericValue.toString()
    : numericValue.toFixed(3);
};

const formatValue = (value) => {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return String(value);
};

const MAX_CHART_FIELDS = 12;
const BAR_COLOR = "#f26b38";
const LINE_COLOR = "#1da1a7";

const toNumber = (value) => {
  const numericValue = Number(value);
  return Number.isNaN(numericValue) ? 0 : numericValue;
};

const buildBarOption = (categories, values, unit, color) => ({
  tooltip: {
    trigger: "axis",
  },
  grid: {
    left: 20,
    right: 20,
    top: 20,
    bottom: 40,
    containLabel: true,
  },
  xAxis: {
    type: "category",
    data: categories,
    axisLabel: {
      rotate: 25,
    },
  },
  yAxis: {
    type: "value",
    axisLabel: {
      formatter: unit ? `{value}${unit}` : "{value}",
    },
  },
  series: [
    {
      type: "bar",
      data: values,
      itemStyle: {
        color: color || BAR_COLOR,
      },
      barMaxWidth: 36,
    },
  ],
});

const buildLineOption = (categories, values, unit, color) => ({
  tooltip: {
    trigger: "axis",
  },
  grid: {
    left: 20,
    right: 20,
    top: 20,
    bottom: 40,
    containLabel: true,
  },
  xAxis: {
    type: "category",
    data: categories,
    axisLabel: {
      rotate: 25,
    },
  },
  yAxis: {
    type: "value",
    axisLabel: {
      formatter: unit ? `{value}${unit}` : "{value}",
    },
  },
  series: [
    {
      type: "line",
      data: values,
      smooth: true,
      symbol: "circle",
      symbolSize: 8,
      lineStyle: {
        color: color || LINE_COLOR,
        width: 3,
      },
      itemStyle: {
        color: color || LINE_COLOR,
      },
      areaStyle: {
        color: "rgba(29, 161, 167, 0.15)",
      },
    },
  ],
});

const buildPieOption = (labels, values) => ({
  tooltip: {
    trigger: "item",
    formatter: "{b}: {c}",
  },
  legend: {
    bottom: 0,
  },
  series: [
    {
      type: "pie",
      radius: ["35%", "65%"],
      data: labels.map((label, index) => ({
        name: label,
        value: values[index],
      })),
      itemStyle: {
        borderRadius: 8,
        borderColor: "#fff",
        borderWidth: 2,
      },
    },
  ],
});

const buildHistogramSlides = (report) => {
  const histograms = report?.histograms || {};
  const entries = Object.entries(histograms);

  if (!entries.length) {
    return [];
  }

  return entries.slice(0, MAX_CHART_FIELDS).map(([field, data]) => {
    const bins = data?.bins || [];
    const counts = data?.counts || [];
    const labels = bins.slice(0, -1).map((value, index) => {
      const start = Number(value);
      const end = Number(bins[index + 1]);

      if (Number.isNaN(start) || Number.isNaN(end)) {
        return `Bin ${index + 1}`;
      }

      return `${start.toFixed(2)} - ${end.toFixed(2)}`;
    });

    return {
      title: `${t("analysisHistogram")} · ${field}`,
      option: {
        tooltip: {
          trigger: "axis",
        },
        grid: {
          left: 20,
          right: 20,
          top: 20,
          bottom: 40,
          containLabel: true,
        },
        xAxis: {
          type: "category",
          data: labels,
          axisLabel: {
            rotate: 25,
          },
        },
        yAxis: {
          type: "value",
        },
        series: [
          {
            type: "bar",
            data: counts,
            itemStyle: {
              color: BAR_COLOR,
            },
            barMaxWidth: 36,
          },
          {
            type: "line",
            data: counts,
            smooth: true,
            symbol: "circle",
            symbolSize: 8,
            lineStyle: {
              color: LINE_COLOR,
              width: 3,
            },
            itemStyle: {
              color: LINE_COLOR,
            },
          },
        ],
      },
    };
  });
};

const buildNumericSlides = (report, metricKey, label) => {
  const summary = report?.numeric_summary || {};
  const entries = Object.entries(summary);

  if (!entries.length) {
    return [];
  }

  const limited = entries.slice(0, MAX_CHART_FIELDS);
  const categories = limited.map(([field]) => field);
  const values = limited.map(([, stats]) => toNumber(stats?.[metricKey]));

  return [
    {
      title: `${label} · ${t("chartTypeBar")}`,
      option: buildBarOption(categories, values, "", BAR_COLOR),
    },
    {
      title: `${label} · ${t("chartTypeLine")}`,
      option: buildLineOption(categories, values, "", LINE_COLOR),
    },
  ];
};

const buildMissingRateSlides = (report) => {
  const entries = Object.entries(report.missing_rate || {});
  if (!entries.length) {
    return [];
  }

  const limited = entries.slice(0, MAX_CHART_FIELDS);
  const categories = limited.map(([field]) => field);
  const values = limited.map(([, value]) => toNumber(value) * 100);

  return [
    {
      title: `${t("analysisMissingRate")} · ${t("chartTypeBar")}`,
      option: buildBarOption(categories, values, "%", BAR_COLOR),
    },
    {
      title: `${t("analysisMissingRate")} · ${t("chartTypeLine")}`,
      option: buildLineOption(categories, values, "%", LINE_COLOR),
    },
  ];
};

const buildTypeDistributionSlides = (report) => {
  const dtypes = report.dtypes || {};
  const counts = {};

  Object.values(dtypes).forEach((dtype) => {
    counts[dtype] = (counts[dtype] || 0) + 1;
  });

  const entries = Object.entries(counts);
  if (!entries.length) {
    return [];
  }

  const labels = entries.map(([dtype]) => dtype);
  const values = entries.map(([, count]) => count);

  return [
    {
      title: `${t("analysisTypeDistribution")} · ${t("chartTypeBar")}`,
      option: buildBarOption(labels, values, "", BAR_COLOR),
    },
    {
      title: `${t("analysisTypeDistribution")} · ${t("chartTypePie")}`,
      option: buildPieOption(labels, values),
    },
  ];
};

const buildChartSlides = (report, chartFlags) => {
  if (!report || !chartFlags) {
    return [];
  }

  const slides = [];

  if (chartFlags.missing_rate) {
    slides.push(...buildMissingRateSlides(report));
  }

  if (chartFlags.histogram_distribution) {
    slides.push(...buildHistogramSlides(report));
  }

  if (chartFlags.numeric_mean) {
    slides.push(...buildNumericSlides(report, "mean", t("analysisNumericMean")));
  }

  if (chartFlags.numeric_max) {
    slides.push(...buildNumericSlides(report, "max", t("analysisNumericMax")));
  }

  if (chartFlags.numeric_min) {
    slides.push(...buildNumericSlides(report, "min", t("analysisNumericMin")));
  }

  if (chartFlags.dtype_distribution) {
    slides.push(...buildTypeDistributionSlides(report));
  }

  return slides;
};

const renderChart = () => {
  if (!chartEl.value) {
    return;
  }

  if (!hasCharts.value) {
    if (chartInstance.value) {
      chartInstance.value.clear();
    }
    return;
  }

  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartEl.value);
  }

  const option = chartSlides.value[chartIndex.value]?.option;
  if (option) {
    chartInstance.value.setOption(option, true);
  }
};

const resizeChart = () => {
  if (chartInstance.value) {
    chartInstance.value.resize();
  }
};

const toggleChartPicker = () => {
  if (!hasCharts.value) {
    return;
  }

  showChartPicker.value = !showChartPicker.value;
};

const selectChart = (index) => {
  if (!hasCharts.value) {
    return;
  }

  chartIndex.value = index;
};

const toggleFields = () => {
  showAllFields.value = !showAllFields.value;
};

const toggleSettingsMenu = () => {
  showSettingsMenu.value = !showSettingsMenu.value;
};

const setLanguage = (value) => {
  locale.value = value;
  showSettingsMenu.value = false;
};

const setSelectionMode = (value) => {
  selectionMode.value = value;
  showSettingsMenu.value = false;
};

const normalizeSelection = (value) => {
  const normalized = {
    preview: Boolean(value.preview),
    report: Boolean(value.report),
    sample: Boolean(value.sample) && Boolean(value.report),
    charts: { ...value.charts },
  };

  if (!normalized.report) {
    normalized.sample = false;
  }

  return normalized;
};

const cloneSelection = (value) => JSON.parse(JSON.stringify(value));

const openSelection = () => {
  if (!selectedFile.value || isUploading.value) {
    return;
  }

  selection.value = cloneSelection(appliedSelection.value);
  showSelection.value = true;
};

const closeSelection = () => {
  showSelection.value = false;
};

const confirmSelection = async () => {
  const normalized = normalizeSelection(selection.value);
  appliedSelection.value = normalized;
  showSelection.value = false;
  chartIndex.value = 0;
  showChartPicker.value = false;
  await runUpload();
};

watch(reportData, () => {
  chartIndex.value = 0;
  nextTick(renderChart);
});

watch(
  () => selection.value.report,
  (value) => {
    if (!value) {
      selection.value.sample = false;
    }
  }
);

watch(chartSlides, (slides) => {
  if (chartIndex.value >= slides.length) {
    chartIndex.value = 0;
  }
  nextTick(renderChart);
});

watch(chartIndex, () => {
  nextTick(renderChart);
});

watch(locale, () => {
  nextTick(renderChart);
});

watch(showChartSection, (value) => {
  if (!value && chartInstance.value) {
    chartInstance.value.dispose();
    chartInstance.value = null;
  }

  if (!value) {
    showChartPicker.value = false;
  }

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

const onFileChange = (event) => {
  const [file] = event.target.files || [];
  selectedFile.value = file || null;
  preview.value = null;
  errorMessage.value = "";
  showAllFields.value = false;
  hasParsed.value = false;
};

const runUpload = async () => {
  if (!selectedFile.value) {
    return;
  }

  isUploading.value = true;
  errorMessage.value = "";

  try {
    preview.value = await uploadDataset(selectedFile.value);
    showAllFields.value = false;
    hasParsed.value = true;
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || t("uploadError");
  } finally {
    isUploading.value = false;
  }
};
</script>
