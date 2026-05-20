<template>
  <div v-if="loading" class="loading">{{ t("loading") }}</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <div v-else-if="!result" class="empty-state">{{ t("mlEmpty") }}</div>
  <div v-else class="ml-results">
    <div class="ml-summary">
      <div>{{ t("mlTaskType") }}: {{ result.task_type }}</div>
      <div>{{ t("mlModel") }}: {{ result.model_type }}</div>
      <div>{{ t("mlTarget") }}: {{ result.target }}</div>
      <div>{{ t("mlFeatureCount") }}: {{ result.features?.length || 0 }}</div>
      <div>{{ t("mlTrainSize") }}: {{ result.split?.sizes?.train }}</div>
      <div v-if="result.split?.sizes?.val">{{ t("mlValSize") }}: {{ result.split?.sizes?.val }}</div>
      <div>{{ t("mlTestSize") }}: {{ result.split?.sizes?.test }}</div>
    </div>

    <div class="ml-metrics">
      <div class="selection-label">{{ t("mlMetrics") }}</div>
      <table class="report-table">
        <thead>
          <tr>
            <th>{{ t("mlSplit") }}</th>
            <th v-for="column in metricColumns" :key="column.key">{{ column.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in metricRows" :key="row.key">
            <td>{{ row.label }}</td>
            <td v-for="column in metricColumns" :key="column.key">
              {{ formatMetricValue(row.metrics?.[column.key], column.key) }}
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="showMulticlassAucHint" class="selection-hint">
        {{ t("mlRocAucMulticlassHint") }}
      </p>
    </div>

    <div v-if="result.ols" class="ml-ols">
      <div class="selection-label">{{ t("mlOlsTitle") }}</div>
      <div class="ml-ols-summary">
        <span>R2: {{ formatMetric(result.ols.summary?.r2) }}</span>
        <span>Adj R2: {{ formatMetric(result.ols.summary?.adj_r2) }}</span>
        <span>AIC: {{ formatMetric(result.ols.summary?.aic) }}</span>
        <span>BIC: {{ formatMetric(result.ols.summary?.bic) }}</span>
        <span>N: {{ result.ols.summary?.nobs }}</span>
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
            <tr v-for="row in result.ols.table" :key="row.feature">
              <td>{{ row.feature }}</td>
              <td>{{ formatMetric(row['Coef.']) }}</td>
              <td>{{ formatMetric(row['Std.Err.']) }}</td>
              <td>{{ formatMetric(row.t) }}</td>
              <td>{{ formatMetric(row['P>|t|']) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else-if="result.coefficients?.length" class="ml-coef">
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
            <tr v-for="row in result.coefficients || []" :key="row.feature + (row.class ?? '')">
              <td>{{ row.feature }}</td>
              <td>{{ formatMetric(row.coef) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else-if="result.feature_importances?.length" class="ml-coef">
      <div class="selection-label">{{ t("mlImportanceTitle") }}</div>
      <div class="report-table-wrapper">
        <table class="report-table">
          <thead>
            <tr>
              <th>{{ t("mlFeature") }}</th>
              <th>{{ t("mlImportance") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in result.feature_importances || []" :key="row.feature">
              <td>{{ row.feature }}</td>
              <td>{{ formatMetric(row.importance) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else class="empty-state">{{ t("mlNoModelExplanation") }}</div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useI18n } from "../composables/useI18n";

const { t } = useI18n();

const props = defineProps({
  loading: Boolean,
  error: String,
  result: Object,
});

const formatMetric = (value) => {
  if (value === null || value === undefined) return "-";
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  return n.toFixed(4);
};

const isClassification = computed(() => props.result?.task_type === "classification");
const classCount = computed(() => props.result?.classes?.length || 0);
const isMulticlass = computed(() => isClassification.value && classCount.value > 2);

const metricColumns = computed(() => {
  if (isClassification.value) {
    return [
      { key: "accuracy", label: t("mlMetricAcc") },
      { key: "precision", label: t("mlMetricPrecision") },
      { key: "recall", label: t("mlMetricRecall") },
      { key: "f1", label: t("mlMetricF1") },
      { key: "roc_auc", label: t("mlMetricAUC") },
    ];
  }
  return [
    { key: "r2", label: t("mlMetricR2") },
    { key: "mae", label: t("mlMetricMAE") },
    { key: "rmse", label: t("mlMetricRMSE") },
  ];
});

const metricRows = computed(() => {
  const rows = [{ key: "train", label: "train", metrics: props.result?.metrics?.train }];
  if (props.result?.metrics?.val) rows.push({ key: "val", label: "val", metrics: props.result.metrics.val });
  rows.push({ key: "test", label: "test", metrics: props.result?.metrics?.test });
  return rows;
});

const showMulticlassAucHint = computed(() => (
  isMulticlass.value && metricRows.value.some((row) => row.metrics?.roc_auc === undefined)
));

const formatMetricValue = (value, key) => {
  if (key === "roc_auc" && value === undefined && isMulticlass.value) {
    return t("mlRocAucMulticlassNotComputed");
  }
  return formatMetric(value);
};
</script>
