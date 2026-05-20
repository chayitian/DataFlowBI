<template>
  <div v-if="show" class="selection-overlay" @click.self="$emit('close')">
    <div
      :class="[
        'selection-panel',
        'feature-engineering-panel',
        selectionMode === 'drawer' ? 'is-drawer' : 'is-dialog',
      ]"
    >
      <div class="selection-header">
        <h3>{{ t("featureEngineeringTitle") }}</h3>
        <button class="icon-button" type="button" @click="$emit('close')">×</button>
      </div>
      <div class="selection-body">
        <div v-if="loading" class="loading">{{ t("loading") }}</div>
        <div v-else class="feature-engineering-body">
          <div class="selection-group">
            <div class="selection-label">{{ t("featureEngineeringNumeric") }}</div>
            <p class="selection-hint">{{ t("featureEngineeringNumericHint") }}</p>
            <div v-if="numericFields.length" class="feature-engineering-actions">
              <button class="ghost-button" type="button" @click="applyNumericToAll('standardize')">
                {{ t("featureEngineeringAllStandardize") }}
              </button>
              <button class="ghost-button" type="button" @click="applyNumericToAll('normalize')">
                {{ t("featureEngineeringAllNormalize") }}
              </button>
              <button class="ghost-button" type="button" @click="applyNumericToAll('')">
                {{ t("featureEngineeringClearNumeric") }}
              </button>
            </div>
            <div v-if="numericFields.length" class="feature-engineering-list">
              <div v-for="field in numericFields" :key="field" class="feature-engineering-row">
                <span class="feature-engineering-field">{{ field }}</span>
                <select v-model="numericTransforms[field]" class="clean-select">
                  <option value="">{{ t("cleanNone") }}</option>
                  <option value="standardize">{{ t("featureEngineeringStandardize") }}</option>
                  <option value="normalize">{{ t("featureEngineeringNormalize") }}</option>
                </select>
              </div>
            </div>
            <p v-else class="selection-hint">{{ t("featureEngineeringNoNumeric") }}</p>
          </div>

          <div class="selection-group">
            <div class="selection-label">{{ t("featureEngineeringCategorical") }}</div>
            <p class="selection-hint">{{ t("featureEngineeringCategoricalHint") }}</p>
            <div v-if="categoricalFields.length" class="feature-engineering-actions">
              <button class="ghost-button" type="button" @click="selectAllCategorical">
                {{ t("selectAll") }}
              </button>
              <button class="ghost-button" type="button" @click="clearCategorical">
                {{ t("clearSelection") }}
              </button>
            </div>
            <div v-if="categoricalFields.length" class="feature-engineering-grid">
              <label v-for="field in categoricalFields" :key="field" class="checkbox">
                <input type="checkbox" :value="field" v-model="selectedCategoricalFields" />
                <span>{{ field }}</span>
              </label>
            </div>
            <p v-else class="selection-hint">{{ t("featureEngineeringNoCategorical") }}</p>
          </div>

          <div class="selection-group">
            <div class="selection-label">{{ t("featureEngineeringDatetime") }}</div>
            <p class="selection-hint">{{ t("featureEngineeringDatetimeHint") }}</p>
            <div v-if="datetimeFields.length" class="feature-engineering-actions">
              <button class="ghost-button" type="button" @click="selectAllDatetime">
                {{ t("selectAll") }}
              </button>
              <button class="ghost-button" type="button" @click="clearDatetime">
                {{ t("clearSelection") }}
              </button>
            </div>
            <div v-if="datetimeFields.length" class="feature-engineering-grid">
              <label v-for="field in datetimeFields" :key="field" class="checkbox">
                <input type="checkbox" :value="field" v-model="selectedDatetimeFields" />
                <span>{{ field }}</span>
              </label>
            </div>
            <p v-else class="selection-hint">{{ t("featureEngineeringNoDatetime") }}</p>
          </div>

          <p v-if="error" class="error">{{ error }}</p>
        </div>
      </div>
      <div class="selection-footer">
        <button class="ghost-button" type="button" @click="$emit('close')">{{ t("cancel") }}</button>
        <button class="primary-btn" type="button" :disabled="!canApply || loading" @click="applyEngineering">
          {{ t("featureEngineeringApply") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
// 这个弹窗收集特征工程选择。后端负责创建新列并保存新快照；上传源文件保持不变。
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "../composables/useI18n";
import { engineerFeatures } from "../api/upload";

const { t } = useI18n();

const props = defineProps({
  show: Boolean,
  fields: { type: Array, default: () => [] },
  filterInfo: Object,
  savedName: String,
  selectionMode: String,
});

const emit = defineEmits(["close", "engineered"]);

const loading = ref(false);
const error = ref("");
const numericTransforms = reactive({});
const selectedCategoricalFields = ref([]);
const selectedDatetimeFields = ref([]);

const fieldDtype = (field) => props.filterInfo?.[field]?.dtype || "";

const isNumeric = (field) => {
  // 数值变换只展示给 int/float 类字段。
  const dtype = fieldDtype(field);
  return dtype.startsWith("int") || dtype.startsWith("float");
};

const isDatetimeCandidate = (field) => {
  // 后端类型建议允许日期字符串字段出现在日期选项中。
  const info = props.filterInfo?.[field] || {};
  const dtype = info.dtype || "";
  return dtype.includes("datetime") || info.suggested_type === "datetime";
};

const numericFields = computed(() => props.fields.filter(isNumeric));
const datetimeFields = computed(() => props.fields.filter(isDatetimeCandidate));
const categoricalFields = computed(() => (
  props.fields.filter((field) => !isNumeric(field) && !datetimeFields.value.includes(field))
));

const selectedNumericTransforms = computed(() => {
  // 把表单对象转换成紧凑的 API payload 结构。
  const payload = {};
  for (const [field, method] of Object.entries(numericTransforms)) {
    if (method) payload[field] = method;
  }
  return payload;
});

const canApply = computed(() => (
  Object.keys(selectedNumericTransforms.value).length > 0
  || selectedCategoricalFields.value.length > 0
  || selectedDatetimeFields.value.length > 0
));

const initState = () => {
  // 每次新数据集或面板重新打开时重置选择。
  for (const key of Object.keys(numericTransforms)) delete numericTransforms[key];
  for (const field of numericFields.value) numericTransforms[field] = "";
  selectedCategoricalFields.value = [];
  selectedDatetimeFields.value = [];
  error.value = "";
};

const applyNumericToAll = (method) => {
  // 批量操作：标准化、归一化或清空所有数值字段。
  for (const field of numericFields.value) numericTransforms[field] = method;
};

const selectAllCategorical = () => {
  selectedCategoricalFields.value = [...categoricalFields.value];
};

const clearCategorical = () => {
  selectedCategoricalFields.value = [];
};

const selectAllDatetime = () => {
  selectedDatetimeFields.value = [...datetimeFields.value];
};

const clearDatetime = () => {
  selectedDatetimeFields.value = [];
};

watch(() => props.show, (value) => {
  if (value) initState();
}, { immediate: true });

watch(numericFields, () => {
  if (props.show) initState();
});

const applyEngineering = async () => {
  // 发出后端结果，让 App.vue 刷新预览和 ML 特征列表。
  if (!props.savedName || !canApply.value) return;
  loading.value = true;
  error.value = "";
  try {
    const result = await engineerFeatures(
      props.savedName,
      selectedNumericTransforms.value,
      selectedCategoricalFields.value,
      selectedDatetimeFields.value,
    );
    emit("engineered", result);
  } catch (e) {
    error.value = e?.response?.data?.detail || t("featureEngineeringFailed");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.feature-engineering-panel { max-width: 640px; }
.feature-engineering-body {
  display: grid;
  gap: 20px;
}
.feature-engineering-list {
  display: grid;
  gap: 8px;
}
.feature-engineering-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.feature-engineering-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.feature-engineering-field {
  min-width: 160px;
  font-weight: 600;
  font-size: 13px;
  color: #333;
}
.feature-engineering-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px 14px;
}
.clean-select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
}
.loading { text-align: center; padding: 20px; color: #888; }
</style>
