<template>
  <div v-if="show" class="selection-overlay" @click.self="$emit('close')">
    <div
      :class="[
        'selection-panel',
        selectionMode === 'drawer' ? 'is-drawer' : 'is-dialog',
      ]"
    >
      <div class="selection-header">
        <h3>{{ t("mlTitle") }}</h3>
        <button class="icon-button" type="button" @click="$emit('close')">×</button>
      </div>
      <div class="selection-body">
        <div class="selection-group">
          <div class="selection-label">{{ t("mlTaskType") }}</div>
          <div class="ml-option-row">
            <label class="checkbox">
              <input type="radio" name="task" value="regression" v-model="taskType" />
              <span>{{ t("mlTaskRegression") }}</span>
            </label>
            <label class="checkbox">
              <input type="radio" name="task" value="classification" v-model="taskType" />
              <span>{{ t("mlTaskClassification") }}</span>
            </label>
          </div>
        </div>

        <div class="selection-group">
          <div class="selection-label">{{ t("mlTarget") }}</div>
          <select v-model="target" class="chart-select">
            <option value="">{{ t("mlChooseTarget") }}</option>
            <option v-for="field in fields" :key="field" :value="field">{{ field }}</option>
          </select>
        </div>

        <div class="selection-group">
          <div class="selection-label">{{ t("mlFeatures") }}</div>
          <div class="ml-option-row">
            <button class="ghost-button" type="button" @click="selectAll">
              {{ t("selectAll") }}
            </button>
            <button class="ghost-button" type="button" @click="clearAll">
              {{ t("mlClearFeatures") }}
            </button>
          </div>
          <div class="ml-feature-grid">
            <label v-for="field in featureOptions" :key="field" class="checkbox">
              <input type="checkbox" :value="field" v-model="features" />
              <span>{{ field }}</span>
            </label>
          </div>
        </div>

        <div class="selection-group">
          <div class="selection-label">{{ t("mlSplitStrategy") }}</div>
          <div class="ml-option-row">
            <label class="checkbox">
              <input type="radio" name="split" value="random" v-model="splitStrategy" />
              <span>{{ t("mlSplitRandom") }}</span>
            </label>
            <label class="checkbox">
              <input type="radio" name="split" value="time_series" v-model="splitStrategy" />
              <span>{{ t("mlSplitTimeSeries") }}</span>
            </label>
          </div>
        </div>

        <div v-if="splitStrategy === 'time_series'" class="selection-group">
          <div class="selection-label">{{ t("mlTimeColumn") }}</div>
          <select v-model="timeColumn" class="chart-select">
            <option value="">{{ t("mlChooseTime") }}</option>
            <option v-for="field in timeOptions" :key="field" :value="field">{{ field }}</option>
          </select>
        </div>

        <div class="selection-group">
          <div class="selection-label">{{ t("mlSplitRatio") }}</div>
          <div class="ml-split-row">
            <label>
              {{ t("mlTestSize") }}
              <input type="number" min="0.05" max="0.5" step="0.05" v-model.number="testSize" />
            </label>
            <label class="checkbox">
              <input type="checkbox" v-model="useValidation" />
              <span>{{ t("mlUseValidation") }}</span>
            </label>
            <label v-if="useValidation">
              {{ t("mlValSize") }}
              <input type="number" min="0.0" max="0.4" step="0.05" v-model.number="valSize" />
            </label>
          </div>
          <p class="ml-split-hint">
            {{ t("mlTrainSize") }}: {{ trainSize.toFixed(2) }}
          </p>
        </div>

        <div class="selection-group">
          <div class="selection-label">{{ t("mlModel") }}</div>
          <select v-model="modelType" class="chart-select">
            <option v-for="option in modelOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <div class="ml-params" v-if="showAlpha">
            <label>
              alpha
              <input type="number" step="0.1" min="0.0" v-model.number="alpha" />
            </label>
          </div>
          <div class="ml-params" v-if="showL1Ratio">
            <label>
              l1_ratio
              <input type="number" step="0.1" min="0" max="1" v-model.number="l1Ratio" />
            </label>
          </div>
          <div class="ml-params" v-if="showC">
            <label>
              C
              <input type="number" step="0.1" min="0.1" v-model.number="cValue" />
            </label>
          </div>
        </div>

        <p v-if="invalidMessage" class="error">{{ invalidMessage }}</p>
      </div>
      <div class="selection-footer">
        <button class="ghost-button" type="button" @click="$emit('close')">
          {{ t("cancel") }}
        </button>
        <button class="primary-btn" type="button" :disabled="!canTrain" @click="handleTrain">
          {{ t("mlTrain") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useI18n } from "../composables/useI18n";

const { t } = useI18n();

const props = defineProps({
  show: Boolean,
  selectionMode: String,
  fields: { type: Array, default: () => [] },
  filterInfo: Object,
});

const emit = defineEmits(["close", "train"]);

const taskType = ref("regression");
const target = ref("");
const features = ref([]);
const splitStrategy = ref("random");
const timeColumn = ref("");
const testSize = ref(0.2);
const useValidation = ref(true);
const valSize = ref(0.1);
const modelType = ref("linear");
const alpha = ref(1.0);
const l1Ratio = ref(0.5);
const cValue = ref(1.0);

const featureOptions = computed(() => props.fields.filter((f) => f !== target.value));
const timeOptions = computed(() => {
  const info = props.filterInfo || {};
  const suggested = Object.entries(info)
    .filter(([, meta]) => meta.suggested_type === "datetime")
    .map(([field]) => field);
  return suggested.length ? suggested : props.fields;
});

const modelOptions = computed(() => {
  if (taskType.value === "classification") {
    return [
      { value: "logistic_l2", label: t("mlModelLogisticL2") },
      { value: "logistic_l1", label: t("mlModelLogisticL1") },
      { value: "logistic_elasticnet", label: t("mlModelLogisticEN") },
    ];
  }
  return [
    { value: "linear", label: t("mlModelLinear") },
    { value: "lasso", label: t("mlModelLasso") },
    { value: "ridge", label: t("mlModelRidge") },
    { value: "elasticnet", label: t("mlModelEN") },
  ];
});

const showAlpha = computed(() => ["lasso", "ridge", "elasticnet"].includes(modelType.value));
const showL1Ratio = computed(() => modelType.value === "elasticnet" || modelType.value === "logistic_elasticnet");
const showC = computed(() => taskType.value === "classification");

const trainSize = computed(() => {
  const val = useValidation.value ? valSize.value : 0;
  return 1 - testSize.value - val;
});

const invalidMessage = computed(() => {
  if (!target.value) return t("mlNeedTarget");
  if (!features.value.length) return t("mlNeedFeatures");
  if (splitStrategy.value === "time_series" && !timeColumn.value) return t("mlNeedTime");
  if (trainSize.value <= 0) return t("mlInvalidSplit");
  return "";
});

const canTrain = computed(() => !invalidMessage.value);

const selectAll = () => {
  features.value = [...featureOptions.value];
};

const clearAll = () => {
  features.value = [];
};

const handleTrain = () => {
  if (!canTrain.value) return;
  emit("train", {
    task_type: taskType.value,
    target: target.value,
    features: features.value,
    split_strategy: splitStrategy.value,
    time_column: splitStrategy.value === "time_series" ? timeColumn.value : null,
    test_size: testSize.value,
    val_size: useValidation.value ? valSize.value : null,
    model_type: modelType.value,
    params: {
      alpha: alpha.value,
      l1_ratio: l1Ratio.value,
      c: cValue.value,
    },
  });
};

watch(
  () => props.show,
  (val) => {
    if (!val) return;
    if (!target.value && props.fields.length) target.value = props.fields[0];
    if (!features.value.length && props.fields.length) {
      features.value = props.fields.filter((f) => f !== target.value);
    }
  }
);

watch(taskType, () => {
  modelType.value = taskType.value === "classification" ? "logistic_l2" : "linear";
});

watch(target, () => {
  if (features.value.includes(target.value)) {
    features.value = features.value.filter((f) => f !== target.value);
  }
});
</script>
