<template>
  <div class="page">
    <div class="top-actions">
      <div class="lang-menu">
        <button class="lang-button" type="button" @click="toggleLangMenu">
          {{ t("settings") }}
        </button>
        <div v-if="showLangMenu" class="lang-dropdown">
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
            @click="submitUpload"
          >
            {{ isUploading ? t("uploading") : t("parseData") }}
          </button>
        </div>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      </div>

      <div class="hero-card">
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
            v-for="field in preview.fields"
            :key="field"
            class="field-chip"
          >
            {{ field }}
          </span>
        </div>
      </div>
    </header>

    <section class="chart-section">
      <div class="chart-header">
        <h2>{{ t("chartTitle") }}</h2>
        <p>{{ t("chartSubtitle") }}</p>
      </div>
      <div class="chart-placeholder">
        <div class="chart-grid">
          <div class="chart-block"></div>
          <div class="chart-block"></div>
          <div class="chart-block"></div>
        </div>
        <span>{{ t("chartPlaceholder") }}</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { uploadDataset } from "./api/upload";

const locale = ref("zh");
const showLangMenu = ref(false);

const messages = {
  zh: {
    settings: "设置",
    language: "语言",
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
    chartTitle: "ECharts 图表区",
    chartSubtitle: "预留后续统计分析与可视化。",
    chartPlaceholder: "图表占位",
    uploadError: "上传失败，请检查服务是否启动。",
  },
  en: {
    settings: "Settings",
    language: "Language",
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
    chartTitle: "ECharts Canvas",
    chartSubtitle: "Reserved for upcoming statistics and visuals.",
    chartPlaceholder: "Chart placeholder",
    uploadError: "Upload failed. Please check the server and try again.",
  },
};

const selectedFile = ref(null);
const preview = ref(null);
const isUploading = ref(false);
const errorMessage = ref("");

const t = (key) => messages[locale.value]?.[key] ?? key;

const toggleLangMenu = () => {
  showLangMenu.value = !showLangMenu.value;
};

const setLanguage = (value) => {
  locale.value = value;
  showLangMenu.value = false;
};

const onFileChange = (event) => {
  const [file] = event.target.files || [];
  selectedFile.value = file || null;
  preview.value = null;
  errorMessage.value = "";
};

const submitUpload = async () => {
  if (!selectedFile.value) {
    return;
  }

  isUploading.value = true;
  errorMessage.value = "";

  try {
    preview.value = await uploadDataset(selectedFile.value);
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || t("uploadError");
  } finally {
    isUploading.value = false;
  }
};
</script>
