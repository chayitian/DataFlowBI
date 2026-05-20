<template>
  <div v-if="show" class="selection-overlay" @click.self="$emit('close')">
    <div
      :class="[
        'selection-panel',
        'clean-panel',
        selectionMode === 'drawer' ? 'is-drawer' : 'is-dialog',
      ]"
    >
      <div class="selection-header">
        <h3>{{ t("cleanTitle") }}</h3>
        <button class="icon-button" type="button" @click="$emit('close')">×</button>
      </div>
      <div class="selection-body">
        <div v-if="loading" class="loading">{{ t("loading") }}</div>
        <div v-else>
          <div class="selection-group">
            <div class="selection-label">{{ t("cleanTemplates") }}</div>
            <div class="clean-template-row">
              <select v-model="selectedTemplate" class="clean-select">
                <option value="">{{ t("cleanTemplateChoose") }}</option>
                <option v-for="tpl in templates" :key="tpl.id" :value="tpl.id">
                  {{ templateLabel(tpl) }}
                </option>
              </select>
              <button
                class="ghost-button"
                type="button"
                @click="applyTemplate"
                :disabled="!selectedTemplate"
              >
                {{ t("cleanApplyTemplate") }}
              </button>
              <button class="ghost-button" type="button" @click="resetTemplate">
                {{ t("cleanResetTemplate") }}
              </button>
            </div>
            <p v-if="templateDescription" class="clean-template-desc">{{ templateDescription }}</p>
          </div>

          <div v-if="qualityFields.length" class="selection-group">
            <div class="selection-label">{{ t("cleanQuality") }}</div>
            <div class="clean-quality-summary">
              <span>{{ t("cleanQualityOverall") }}: {{ formatScore(overallQuality) }}</span>
            </div>
            <div class="clean-quality-list">
              <div v-for="item in qualityFields" :key="item.field" class="clean-quality-row">
                <span class="clean-quality-field">{{ item.field }}</span>
                <span class="clean-quality-score">{{ formatScore(item.score) }}</span>
                <span class="clean-quality-meta">{{ t("missingRateLabel") }}: {{ formatPercent(item.missing_rate) }}</span>
                <span class="clean-quality-meta">{{ t("cleanOutlierRate") }}: {{ formatPercent(item.outlier_rate) }}</span>
              </div>
            </div>
          </div>

          <div class="selection-group">
            <div class="clean-section-tabs">
              <button
                :class="['clean-section-tab', { active: activeCleanSection === 'missing' }]"
                type="button"
                @click="activeCleanSection = 'missing'"
              >
                {{ t("cleanMissing") }}
              </button>
              <button
                :class="['clean-section-tab', { active: activeCleanSection === 'outliers' }]"
                type="button"
                @click="activeCleanSection = 'outliers'"
              >
                {{ t("cleanOutliers") }}
              </button>
              <button
                :class="['clean-section-tab', { active: activeCleanSection === 'types' }]"
                type="button"
                @click="activeCleanSection = 'types'"
              >
                {{ t("cleanTypeConversion") }}
              </button>
            </div>
          </div>

          <div v-if="activeCleanSection === 'missing'" class="selection-group">
            <div class="selection-label">{{ t("cleanMissing") }}</div>
            <div v-for="field in fields" :key="field" class="clean-field-row">
              <span class="clean-field-name">{{ field }} ({{ fieldDtype(field) }})</span>
              <select v-model="missingConfigs[field].method" class="clean-select">
                <option value="">{{ t("cleanNone") }}</option>
                <option value="drop">{{ t("cleanDrop") }}</option>
                <option value="fill_mean">{{ t("cleanFillMean") }}</option>
                <option value="fill_median">{{ t("cleanFillMedian") }}</option>
                <option value="fill_mode">{{ t("cleanFillMode") }}</option>
                <option value="fill_value">{{ t("cleanFillValue") }}</option>
                <option value="fill_ffill">{{ t("cleanFillForward") }}</option>
                <option value="fill_bfill">{{ t("cleanFillBackward") }}</option>
              </select>
              <input
                v-if="missingConfigs[field].method === 'fill_value'"
                v-model="missingConfigs[field].value"
                class="clean-input"
                :placeholder="t('cleanValuePlaceholder')"
              />
            </div>
          </div>
          <div v-if="activeCleanSection === 'outliers'" class="selection-group">
            <div class="selection-label">{{ t("cleanOutliers") }}</div>
            <div v-for="field in numericFields" :key="'out-'+field" class="clean-field-row">
              <span class="clean-field-name">{{ field }}</span>
              <select v-model="outlierConfigs[field].method" class="clean-select">
                <option value="">{{ t("cleanNone") }}</option>
                <option value="iqr">{{ t("cleanIQR") }}</option>
                <option value="zscore">{{ t("cleanZScore") }}</option>
              </select>
              <span v-if="outlierConfigs[field].method" class="clean-label">{{ t("cleanThreshold") }}</span>
              <input
                v-if="outlierConfigs[field].method"
                v-model.number="outlierConfigs[field].threshold"
                type="number"
                step="0.1"
                min="0.1"
                class="clean-input clean-input--narrow"
              />
              <select v-if="outlierConfigs[field].method" v-model="outlierConfigs[field].action" class="clean-select">
                <option value="remove">{{ t("cleanRemove") }}</option>
                <option value="cap">{{ t("cleanCap") }}</option>
              </select>
            </div>
          </div>
          <div v-if="activeCleanSection === 'types'" class="selection-group">
            <div class="selection-label">{{ t("cleanTypeConversion") }}</div>
            <div v-for="field in fields" :key="'tc-'+field" class="clean-field-row">
              <span class="clean-field-name">{{ field }} ({{ fieldDtype(field) }})</span>
              <select v-model="typeConversions[field]" class="clean-select">
                <option value="">{{ t("cleanNone") }}</option>
                <option value="int">int</option>
                <option value="float">float</option>
                <option value="str">str</option>
                <option value="datetime">datetime</option>
              </select>
              <span v-if="typeSuggestion(field)" class="clean-suggestion">{{ typeSuggestion(field) }}</span>
            </div>
          </div>
          <div v-if="comparison" class="selection-group">
            <div class="selection-label">{{ t("cleanComparison") }}</div>
            <div class="clean-compare">
              <div class="clean-compare-row clean-compare-head">
                <span></span>
                <span>{{ t("cleanBefore") }}</span>
                <span>{{ t("cleanAfter") }}</span>
                <span>{{ t("cleanDelta") }}</span>
              </div>
              <div class="clean-compare-row">
                <span>{{ t("rows") }}</span>
                <span>{{ comparison.before.rows }}</span>
                <span>{{ comparison.after.rows }}</span>
                <span>{{ comparison.delta.rows }}</span>
              </div>
              <div class="clean-compare-row">
                <span>{{ t("cleanMissingRateAvg") }}</span>
                <span>{{ formatPercent(comparison.before.missing_rate_avg) }}</span>
                <span>{{ formatPercent(comparison.after.missing_rate_avg) }}</span>
                <span>{{ formatPercent(comparison.delta.missing_rate_avg) }}</span>
              </div>
              <div class="clean-compare-row">
                <span>{{ t("cleanQualityOverall") }}</span>
                <span>{{ formatScore(comparison.before.quality_overall) }}</span>
                <span>{{ formatScore(comparison.after.quality_overall) }}</span>
                <span>{{ formatScore(comparison.delta.quality_overall) }}</span>
              </div>
            </div>
          </div>
          <div v-if="cleaningLog.length" class="selection-group">
            <div class="selection-label">{{ t("cleanLog") }}</div>
            <div class="clean-log-actions">
              <button class="ghost-button" type="button" @click="exportLog">{{ t("cleanLogExport") }}</button>
            </div>
            <div class="clean-log">
              <div v-for="(log, i) in cleaningLog" :key="i" class="clean-log-item">
                <span class="clean-log-op">{{ log.operation }}</span>
                <span class="clean-log-field">{{ log.field }}</span>
                <span class="clean-log-detail">{{ log.detail || `${log.rows_affected || 0} rows` }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="selection-footer">
        <button class="ghost-button" type="button" @click="$emit('close')">{{ t("cancel") }}</button>
        <button class="primary-btn" type="button" @click="applyClean">{{ t("cleanApply") }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
// CleanPanel 让用户按列配置数据质量操作。它只把选中的规则发送给后端；
// 实际 pandas 修改发生在 backend/app/services/file_preview.py。
import { ref, reactive, computed, watch } from "vue";
import { useI18n } from "../composables/useI18n";
import { cleanData as cleanApi, getCleanTemplates } from "../api/upload";

const { t } = useI18n();

const props = defineProps({
  show: Boolean,
  fields: { type: Array, default: () => [] },
  filterInfo: Object,
  savedName: String,
  quality: Object,
  selectionMode: String,
});

const emit = defineEmits(["close", "cleaned"]);

const loading = ref(false);
const cleaningLog = ref([]);
const comparison = ref(null);
const templates = ref([]);
const selectedTemplate = ref("");
const activeCleanSection = ref("missing");

const missingConfigs = reactive({});
const outlierConfigs = reactive({});
const typeConversions = reactive({});

const numericFields = computed(() => {
  // 离群值规则只适用于数值列。
  if (!props.filterInfo) return [];
  return Object.entries(props.filterInfo)
    .filter(([, meta]) => meta.dtype && (meta.dtype.startsWith("int") || meta.dtype.startsWith("float")))
    .map(([field]) => field);
});

const overallQuality = computed(() => props.quality?.overall ?? null);

const qualityFields = computed(() => {
  // 分数最低的字段排在前面，引导用户优先处理问题列。
  const fields = props.quality?.fields || {};
  return Object.entries(fields)
    .map(([field, meta]) => ({
      field,
      missing_rate: meta.missing_rate ?? 0,
      outlier_rate: meta.outlier_rate ?? 0,
      score: meta.score ?? 0,
    }))
    .sort((a, b) => a.score - b.score);
});

const fieldDtype = (field) => props.filterInfo?.[field]?.dtype || "";

const fieldCategory = (field) => {
  // 模板会按字段大类应用不同的缺失值默认规则。
  const dtype = fieldDtype(field);
  if (dtype.includes("datetime")) return "datetime";
  if (dtype.startsWith("int") || dtype.startsWith("float")) return "numeric";
  return "categorical";
};

const templateDescription = computed(() => {
  const tpl = templates.value.find((t) => t.id === selectedTemplate.value);
  return tpl ? t(tpl.desc_key || "") : "";
});

const templateLabel = (tpl) => t(tpl.label_key || tpl.label || tpl.id);

const initConfigs = () => {
  // 每次打开面板或加载新数据集时重建表单状态。
  for (const key of Object.keys(missingConfigs)) delete missingConfigs[key];
  for (const key of Object.keys(outlierConfigs)) delete outlierConfigs[key];
  for (const key of Object.keys(typeConversions)) delete typeConversions[key];
  for (const field of props.fields) {
    missingConfigs[field] = { method: "", value: "" };
    typeConversions[field] = "";
  }
  for (const field of numericFields.value) {
    outlierConfigs[field] = { method: "", threshold: 1.5, action: "remove" };
  }
  cleaningLog.value = [];
  comparison.value = null;
};

const fetchTemplates = async () => {
  // 模板只是可选的便捷预设；加载失败不应阻止清洗。
  try {
    const data = await getCleanTemplates();
    templates.value = data.templates || [];
  } catch {
    templates.value = [];
  }
};

watch(() => props.show, (val) => {
  if (val) {
    initConfigs();
    selectedTemplate.value = "";
    activeCleanSection.value = "missing";
    fetchTemplates();
  }
}, { immediate: true });

const typeSuggestion = (field) => {
  // 建议来自后端 build_filter_info() 中的类型推断。
  const info = props.filterInfo?.[field];
  if (!info?.suggested_type) return "";
  const conf = info.suggestion_confidence;
  const pct = typeof conf === "number" ? Math.round(conf * 100) : null;
  return pct !== null
    ? `${t("cleanSuggested")} ${info.suggested_type} (${pct}%)`
    : `${t("cleanSuggested")} ${info.suggested_type}`;
};

const applyTemplate = () => {
  // 模板填充的是用户也可以手动选择的同一组控件。
  const tpl = templates.value.find((t) => t.id === selectedTemplate.value);
  if (!tpl) return;

  const missing = tpl.missing || {};
  for (const field of props.fields) {
    const category = fieldCategory(field);
    const rule = missing[category];
    if (rule?.method) {
      missingConfigs[field].method = rule.method;
      missingConfigs[field].value = rule.value ?? "";
    } else {
      missingConfigs[field].method = "";
      missingConfigs[field].value = "";
    }
  }

  const outRule = tpl.outlier?.numeric;
  for (const field of numericFields.value) {
    if (outRule?.method) {
      outlierConfigs[field].method = outRule.method;
      outlierConfigs[field].threshold = outRule.threshold ?? 1.5;
      outlierConfigs[field].action = outRule.action || "remove";
    } else {
      outlierConfigs[field].method = "";
      outlierConfigs[field].threshold = 1.5;
      outlierConfigs[field].action = "remove";
    }
  }

  const typeRule = tpl.type_conversion || {};
  for (const field of props.fields) {
    typeConversions[field] = "";
    if (!typeRule.use_suggestions) continue;
    const info = props.filterInfo?.[field];
    if (!info?.suggested_type) continue;
    const conf = info.suggestion_confidence ?? 0;
    if (conf >= (typeRule.min_confidence ?? 0.0)) {
      typeConversions[field] = info.suggested_type;
    }
  }
};

const resetTemplate = () => {
  selectedTemplate.value = "";
  initConfigs();
};

const formatPercent = (value) => {
  if (value === null || value === undefined) return "-";
  return `${(Number(value) * 100).toFixed(1)}%`;
};

const formatScore = (value) => {
  if (value === null || value === undefined) return "-";
  return Number(value).toFixed(1);
};

const exportLog = () => {
  // 导出最近一次后端清洗日志，便于审计或排查问题。
  if (!cleaningLog.value.length) return;
  const payload = {
    cleaning_log: cleaningLog.value,
    comparison: comparison.value,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "cleaning_log.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

const buildMissingPayload = () => {
  // 只发送启用规则的字段；空配置表示不执行操作。
  const payload = {};
  for (const [field, cfg] of Object.entries(missingConfigs)) {
    if (cfg.method) {
      payload[field] = { method: cfg.method };
      if (cfg.method === "fill_value") payload[field].value = cfg.value;
    }
  }
  return Object.keys(payload).length ? payload : null;
};

const buildOutlierPayload = () => {
  // 保持 payload 简洁，并让后端校验仅数值字段可执行的操作。
  const payload = {};
  for (const [field, cfg] of Object.entries(outlierConfigs)) {
    if (cfg.method) {
      payload[field] = { method: cfg.method, threshold: cfg.threshold, action: cfg.action };
    }
  }
  return Object.keys(payload).length ? payload : null;
};

const buildTypePayload = () => {
  // 类型转换会在后端先于缺失值/离群值处理执行。
  const payload = {};
  for (const [field, target] of Object.entries(typeConversions)) {
    if (target) payload[field] = target;
  }
  return Object.keys(payload).length ? payload : null;
};

const applyClean = async () => {
  // 清洗成功后会返回新的数据集快照和更新后的 report 数据。
  if (!props.savedName) return;
  loading.value = true;
  cleaningLog.value = [];
  try {
    const result = await cleanApi(
      props.savedName,
      buildMissingPayload(),
      buildOutlierPayload(),
      buildTypePayload(),
    );
    cleaningLog.value = result.cleaning_log || [];
    comparison.value = result.comparison || null;
    emit("cleaned", result);
  } catch {
    cleaningLog.value = [{ operation: "error", field: "", detail: "Clean operation failed" }];
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.clean-panel { max-width: 640px; }
.clean-field-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  flex-wrap: wrap;
}
.clean-field-name {
  min-width: 120px;
  font-weight: 600;
  font-size: 13px;
  color: #333;
}
.clean-select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
}
.clean-input {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  width: 120px;
}
.clean-input--narrow { width: 64px; }
.clean-label {
  font-size: 12px;
  color: #888;
}
.clean-log {
  max-height: 200px;
  overflow-y: auto;
  background: #f9fafb;
  border-radius: 8px;
  padding: 8px 12px;
}
.clean-log-actions {
  margin-bottom: 8px;
}
.clean-log-item {
  display: flex;
  gap: 8px;
  font-size: 12px;
  padding: 3px 0;
}
.clean-log-op {
  font-weight: 600;
  color: #3b82f6;
  min-width: 90px;
}
.clean-log-field { color: #555; min-width: 80px; }
.clean-log-detail { color: #888; }
.loading { text-align: center; padding: 20px; color: #888; }
.clean-template-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.clean-template-desc {
  margin-top: 6px;
  font-size: 12px;
  color: #666;
}
.clean-section-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.clean-section-tab {
  border: 1px solid rgba(37, 99, 235, 0.22);
  background: rgba(37, 99, 235, 0.06);
  color: #1d4ed8;
  padding: 8px 14px;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
}
.clean-section-tab.active {
  color: #fff;
  background: linear-gradient(120deg, #2563eb, #3b82f6);
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.18);
}
.clean-suggestion {
  font-size: 12px;
  color: #0f766e;
}
.clean-quality-summary {
  font-size: 13px;
  color: #333;
  margin-bottom: 8px;
}
.clean-quality-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.clean-quality-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #555;
}
.clean-quality-field {
  min-width: 120px;
  font-weight: 600;
}
.clean-quality-score {
  min-width: 60px;
  color: #111827;
}
.clean-quality-meta {
  color: #6b7280;
}
.clean-compare {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
}
.clean-compare-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 4px 0;
}
.clean-compare-head {
  font-weight: 600;
  color: #374151;
}
</style>
