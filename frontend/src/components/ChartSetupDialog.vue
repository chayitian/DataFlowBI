<template>
  <div
    v-if="show"
    class="selection-overlay"
    @click.self="$emit('close')"
  >
    <div
      :class="[
        'selection-panel',
        selectionMode === 'drawer' ? 'is-drawer' : 'is-dialog',
      ]"
    >
      <div class="selection-header">
        <h3>{{ t("chartSetupTitle") }}</h3>
        <button class="icon-button" type="button" @click="$emit('close')">
          ×
        </button>
      </div>
      <div class="selection-body">
        <div class="selection-group">
          <div class="selection-label">{{ t("chartGroupMissing") }}</div>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.missing_rate" @change="toggle('missing_rate')" />
            <span>{{ t("analysisMissingRate") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.missing_heatmap" @change="toggle('missing_heatmap')" />
            <span>{{ t("selectionMissingHeatmap") }}</span>
          </label>
        </div>
        <div class="selection-group">
          <div class="selection-label">{{ t("chartGroupDistribution") }}</div>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.feature_distribution" @change="toggle('feature_distribution')" />
            <span>{{ t("analysisFeatureDistribution") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.dtype_distribution" @change="toggle('dtype_distribution')" />
            <span>{{ t("analysisTypeDistribution") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.violin" @change="toggle('violin')" />
            <span>{{ t("selectionViolin") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.boxplot" @change="toggle('boxplot')" />
            <span>{{ t("selectionBoxplot") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.binning" @change="toggle('binning')" />
            <span>{{ t("selectionBinning") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.frequency" @change="toggle('frequency')" />
            <span>{{ t("selectionFrequency") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.pareto" @change="toggle('pareto')" />
            <span>{{ t("selectionPareto") }}</span>
          </label>
        </div>
        <div class="selection-group">
          <div class="selection-label">{{ t("chartGroupCorrelation") }}</div>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.correlation" @change="toggle('correlation')" />
            <span>{{ t("selectionCorrelation") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.scatter_matrix" @change="toggle('scatter_matrix')" />
            <span>{{ t("selectionScatter") }}</span>
          </label>
        </div>
        <div class="selection-group">
          <div class="selection-label">{{ t("chartGroupAggregation") }}</div>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.group_stats" @change="toggle('group_stats')" />
            <span>{{ t("selectionGroupStats") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.timeseries" @change="toggle('timeseries')" />
            <span>{{ t("selectionTimeseries") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.outliers" @change="toggle('outliers')" />
            <span>{{ t("selectionOutliers") }}</span>
          </label>
        </div>
        <div class="selection-group">
          <div class="selection-label">{{ t("chartGroupNumeric") }}</div>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.numeric_mean" @change="toggle('numeric_mean')" />
            <span>{{ t("analysisNumericMean") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.numeric_max" @change="toggle('numeric_max')" />
            <span>{{ t("analysisNumericMax") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="chartTypes.numeric_min" @change="toggle('numeric_min')" />
            <span>{{ t("analysisNumericMin") }}</span>
          </label>
        </div>
      </div>
      <div class="selection-footer">
        <button class="ghost-button" type="button" @click="$emit('close')">
          {{ t("cancel") }}
        </button>
        <button class="primary-btn" type="button" @click="$emit('confirm')">
          {{ t("chartSetupConfirm") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from "../composables/useI18n";

const props = defineProps({
  show: Boolean,
  chartTypes: Object,
  selectionMode: String,
});

const emit = defineEmits(["close", "confirm", "update:chartTypes"]);

const { t } = useI18n();

const toggle = (key) => {
  emit("update:chartTypes", { ...props.chartTypes, [key]: !props.chartTypes[key] });
};
</script>
