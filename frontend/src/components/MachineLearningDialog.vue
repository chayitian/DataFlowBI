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

          <div class="ml-feature-section">
            <div class="ml-feature-section-header">
              <span>{{ t("mlOriginalFeatures") }}</span>
              <div class="ml-option-row">
                <button class="ghost-button" type="button" @click="selectOriginalFeatures">
                  {{ t("selectAll") }}
                </button>
                <button class="ghost-button" type="button" @click="clearOriginalFeatures">
                  {{ t("clearSelection") }}
                </button>
              </div>
            </div>
            <div v-if="originalFeatureOptions.length" class="ml-feature-grid">
              <label v-for="field in originalFeatureOptions" :key="field" class="checkbox">
                <input type="checkbox" :value="field" v-model="features" />
                <span>{{ field }}</span>
              </label>
            </div>
            <p v-else class="selection-hint">{{ t("mlNoOriginalFeatures") }}</p>
          </div>

          <div class="ml-feature-section">
            <div class="ml-feature-section-header">
              <span>{{ t("mlEngineeredFeatures") }}</span>
              <div class="ml-option-row">
                <button class="ghost-button" type="button" @click="selectEngineeredFeatures">
                  {{ t("selectAll") }}
                </button>
                <button class="ghost-button" type="button" @click="clearEngineeredFeatures">
                  {{ t("clearSelection") }}
                </button>
              </div>
            </div>
            <div v-if="engineeredFeatureOptions.length" class="ml-feature-grid">
              <label v-for="field in engineeredFeatureOptions" :key="field" class="checkbox">
                <input type="checkbox" :value="field" v-model="features" />
                <span>{{ field }}</span>
              </label>
            </div>
            <p v-else class="selection-hint">{{ t("mlNoEngineeredFeatures") }}</p>
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

          <div v-if="modelParamDefinitions.length" class="ml-params-grid">
            <label v-for="param in modelParamDefinitions" :key="param.key">
              <span>{{ param.label }}</span>
              <select v-if="param.type === 'select'" v-model="paramValues[param.key]">
                <option v-for="option in param.options" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <input
                v-else
                type="number"
                :step="param.step ?? 1"
                :min="param.min"
                :max="param.max"
                v-model.number="paramValues[param.key]"
              />
            </label>
          </div>

          <div class="ml-advanced-params">
            <label>
              <span>{{ t("mlAdvancedParams") }}</span>
              <textarea
                v-model="advancedParamsText"
                :placeholder="t('mlAdvancedParamsPlaceholder')"
                rows="3"
              ></textarea>
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
// MachineLearningDialog 负责构建 /ml/train payload。实际 sklearn 预处理和训练由后端负责；
// 本组件专注于收集有效的用户选择。
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "../composables/useI18n";

const { t } = useI18n();

const props = defineProps({
  show: Boolean,
  selectionMode: String,
  fields: { type: Array, default: () => [] },
  originalFields: { type: Array, default: () => [] },
  engineeredFields: { type: Array, default: () => [] },
  filterInfo: Object,
});

const emit = defineEmits(["close", "train"]);

const taskType = ref("regression");
const target = ref("");
const features = ref([]);
const splitStrategy = ref("random");
const timeColumn = ref("");
const testSize = ref(0.2);
const useValidation = ref(false);
const valSize = ref(0.1);
const modelType = ref("linear");
const paramValues = reactive({});
const advancedParamsText = ref("");

const featureOptions = computed(() => props.fields.filter((f) => f !== target.value));
const engineeredSet = computed(() => new Set(props.engineeredFields.filter((f) => props.fields.includes(f))));
const originalFeatureOptions = computed(() => {
  // 为了可读性，原始特征和生成特征分开展示。
  const source = props.originalFields.length
    ? props.originalFields.filter((field) => props.fields.includes(field))
    : props.fields.filter((field) => !engineeredSet.value.has(field));
  return source.filter((field) => field !== target.value);
});
const engineeredFeatureOptions = computed(() => (
  props.fields.filter((field) => field !== target.value && engineeredSet.value.has(field))
));

const timeOptions = computed(() => {
  // 优先使用后端检测到的日期字段，同时允许手动兜底选择。
  const info = props.filterInfo || {};
  const suggested = Object.entries(info)
    .filter(([, meta]) => meta.suggested_type === "datetime")
    .map(([field]) => field);
  return suggested.length ? suggested : props.fields;
});

const modelOptions = computed(() => {
  // 回归和分类支持不同的 sklearn 估计器。
  if (taskType.value === "classification") {
    return [
      { value: "logistic_l2", label: t("mlModelLogisticL2") },
      { value: "logistic_l1", label: t("mlModelLogisticL1") },
      { value: "logistic_elasticnet", label: t("mlModelLogisticEN") },
      { value: "random_forest_classifier", label: t("mlModelRandomForest") },
      { value: "gradient_boosting_classifier", label: t("mlModelGradientBoosting") },
      { value: "svc", label: t("mlModelSVC") },
      { value: "knn_classifier", label: t("mlModelKNN") },
      { value: "decision_tree_classifier", label: t("mlModelDecisionTree") },
      { value: "gaussian_nb", label: t("mlModelGaussianNB") },
    ];
  }
  return [
    { value: "linear", label: t("mlModelLinear") },
    { value: "lasso", label: t("mlModelLasso") },
    { value: "ridge", label: t("mlModelRidge") },
    { value: "elasticnet", label: t("mlModelEN") },
    { value: "random_forest_regressor", label: t("mlModelRandomForest") },
    { value: "gradient_boosting_regressor", label: t("mlModelGradientBoosting") },
    { value: "svr", label: t("mlModelSVR") },
    { value: "knn_regressor", label: t("mlModelKNN") },
    { value: "decision_tree_regressor", label: t("mlModelDecisionTree") },
    { value: "huber", label: t("mlModelHuber") },
  ];
});

const numberParam = (key, defaultValue, options = {}) => ({
  key,
  label: options.label || key,
  type: "number",
  defaultValue,
  ...options,
});

const selectParam = (key, defaultValue, options) => ({
  key,
  label: key,
  type: "select",
  defaultValue,
  options: options.map((value) => ({ value, label: String(value) })),
});

const treeParams = [
  numberParam("n_estimators", 100, { min: 1, step: 1 }),
  numberParam("max_depth", "", { min: 1, step: 1 }),
  numberParam("min_samples_split", 2, { min: 2, step: 1 }),
  numberParam("min_samples_leaf", 1, { min: 1, step: 1 }),
];

const boostingParams = [
  numberParam("n_estimators", 100, { min: 1, step: 1 }),
  numberParam("learning_rate", 0.1, { min: 0.001, step: 0.01 }),
  numberParam("max_depth", 3, { min: 1, step: 1 }),
];

const knnParams = [
  numberParam("n_neighbors", 5, { min: 1, step: 1 }),
  selectParam("weights", "uniform", ["uniform", "distance"]),
  selectParam("metric", "minkowski", ["minkowski", "euclidean", "manhattan"]),
];

const modelParamDefinitions = computed(() => {
  // 参数控件根据所选模型 key 动态生成。
  switch (modelType.value) {
    case "linear":
      return [selectParam("fit_intercept", true, [true, false])];
    case "lasso":
      return [numberParam("alpha", 1.0, { min: 0, step: 0.1 }), numberParam("max_iter", 5000, { min: 100, step: 100 })];
    case "ridge":
      return [numberParam("alpha", 1.0, { min: 0, step: 0.1 })];
    case "elasticnet":
      return [numberParam("alpha", 1.0, { min: 0, step: 0.1 }), numberParam("l1_ratio", 0.5, { min: 0, max: 1, step: 0.1 }), numberParam("max_iter", 5000, { min: 100, step: 100 })];
    case "random_forest_regressor":
    case "random_forest_classifier":
      return treeParams;
    case "gradient_boosting_regressor":
    case "gradient_boosting_classifier":
      return boostingParams;
    case "svr":
      return [numberParam("c", 1.0, { min: 0.001, step: 0.1, label: "C" }), selectParam("kernel", "rbf", ["linear", "rbf", "poly", "sigmoid"]), selectParam("gamma", "scale", ["scale", "auto"]), numberParam("epsilon", 0.1, { min: 0, step: 0.05 })];
    case "svc":
      return [numberParam("c", 1.0, { min: 0.001, step: 0.1, label: "C" }), selectParam("kernel", "rbf", ["linear", "rbf", "poly", "sigmoid"]), selectParam("gamma", "scale", ["scale", "auto"]), numberParam("max_iter", -1, { step: 100 })];
    case "knn_regressor":
    case "knn_classifier":
      return knnParams;
    case "decision_tree_regressor":
      return [numberParam("max_depth", "", { min: 1, step: 1 }), numberParam("min_samples_split", 2, { min: 2, step: 1 }), numberParam("min_samples_leaf", 1, { min: 1, step: 1 }), selectParam("criterion", "squared_error", ["squared_error", "friedman_mse", "absolute_error"])] ;
    case "decision_tree_classifier":
      return [numberParam("max_depth", "", { min: 1, step: 1 }), numberParam("min_samples_split", 2, { min: 2, step: 1 }), numberParam("min_samples_leaf", 1, { min: 1, step: 1 }), selectParam("criterion", "gini", ["gini", "entropy", "log_loss"])] ;
    case "huber":
      return [numberParam("alpha", 0.0001, { min: 0, step: 0.0001 }), numberParam("epsilon", 1.35, { min: 1.0, step: 0.05 }), numberParam("max_iter", 100, { min: 10, step: 10 })];
    case "logistic_l2":
    case "logistic_l1":
      return [numberParam("c", 1.0, { min: 0.001, step: 0.1, label: "C" }), numberParam("max_iter", 2000, { min: 100, step: 100 })];
    case "logistic_elasticnet":
      return [numberParam("c", 1.0, { min: 0.001, step: 0.1, label: "C" }), numberParam("l1_ratio", 0.5, { min: 0, max: 1, step: 0.1 }), numberParam("max_iter", 4000, { min: 100, step: 100 })];
    case "gaussian_nb":
      return [numberParam("var_smoothing", 1e-9, { min: 0, step: 1e-9 })];
    default:
      return [];
  }
});

const trainSize = computed(() => {
  const val = useValidation.value ? valSize.value : 0;
  return 1 - testSize.value - val;
});

const parsedAdvancedParams = computed(() => {
  // 高级 JSON 会覆盖生成控件中的参数，供高级用户使用。
  const text = advancedParamsText.value.trim();
  if (!text) return {};
  try {
    const parsed = JSON.parse(text);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
});

const invalidMessage = computed(() => {
  // 非空提示会禁用训练按钮，并说明原因。
  if (!target.value) return t("mlNeedTarget");
  if (!features.value.length) return t("mlNeedFeatures");
  if (splitStrategy.value === "time_series" && !timeColumn.value) return t("mlNeedTime");
  if (trainSize.value <= 0) return t("mlInvalidSplit");
  if (parsedAdvancedParams.value === null) return t("mlInvalidAdvancedParams");
  return "";
});

const canTrain = computed(() => !invalidMessage.value);

const dedupe = (values) => Array.from(new Set(values));
const addFeatures = (values) => {
  // 选择辅助函数会去重，并避免误选目标字段。
  features.value = dedupe([...features.value, ...values]).filter((field) => featureOptions.value.includes(field));
};
const removeFeatures = (values) => {
  const removeSet = new Set(values);
  features.value = features.value.filter((field) => !removeSet.has(field));
};

const selectAll = () => {
  features.value = [...featureOptions.value];
};

const clearAll = () => {
  features.value = [];
};

const selectOriginalFeatures = () => addFeatures(originalFeatureOptions.value);
const clearOriginalFeatures = () => removeFeatures(originalFeatureOptions.value);
const selectEngineeredFeatures = () => addFeatures(engineeredFeatureOptions.value);
const clearEngineeredFeatures = () => removeFeatures(engineeredFeatureOptions.value);

const initParamValues = () => {
  // 用户切换估计器时重置模型参数。
  for (const key of Object.keys(paramValues)) delete paramValues[key];
  for (const param of modelParamDefinitions.value) {
    paramValues[param.key] = param.defaultValue;
  }
  advancedParamsText.value = "";
};

const buildParams = () => ({
  ...paramValues,
  ...(parsedAdvancedParams.value || {}),
});

const handleTrain = () => {
  // App.vue 会在调用后端接口前补上 saved_name。
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
    params: buildParams(),
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

watch(modelType, initParamValues, { immediate: true });

watch(target, () => {
  if (features.value.includes(target.value)) {
    features.value = features.value.filter((f) => f !== target.value);
  }
});
</script>
