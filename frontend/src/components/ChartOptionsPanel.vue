<template>
  <div v-if="show" class="chart-options">
    <div class="chart-options-left">
      <div class="chart-options-title">{{ t("analysisCategory") }}</div>
      <button
        v-for="option in analysisOptions"
        :key="option.key"
        :class="['chart-option-item', { active: option.key === category }]"
        type="button"
        @click="$emit('selectAnalysis', option.key)"
      >
        <span>{{ option.label }}</span>
        <span
          :class="['chart-option-arrow', { open: option.key === category }]"
        >
          ▾
        </span>
      </button>
    </div>
    <div class="chart-options-right">
      <div class="chart-options-title">{{ t("chartType") }}</div>

      <div v-if="category === 'feature_distribution'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeHistogram") }}</div>
        <div v-if="histogramFields.length" class="chart-feature-list">
          <button
            v-for="feature in histogramFields"
            :key="feature"
            :class="[
              'chart-feature-item',
              { active: comparison ? selecteds.includes(feature) : feature === featureVal },
            ]"
            type="button"
            @click="comparison ? $emit('toggleComparisonField', feature) : $emit('update:feature', feature)"
          >
            {{ feature }}
          </button>
        </div>
        <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
        <div class="histogram-controls">
          <div class="histogram-control-row">
            <label class="histogram-label">{{ t("histogramBins") }}</label>
            <input
              type="range"
              class="histogram-slider"
              :value="binCount"
              min="2"
              max="50"
              @input="$emit('update:binCount', Number($event.target.value))"
            />
            <span class="histogram-value">{{ binCount }}</span>
          </div>
          <label class="checkbox histogram-checkbox">
            <input type="checkbox" :checked="normalize" @change="$emit('update:normalize', $event.target.checked)" />
            <span>{{ t("histogramNormalize") }}</span>
          </label>
        </div>
      </div>

      <div v-else-if="category === 'frequency'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeFrequency") }}</div>
        <div v-if="freqFields.length" class="chart-feature-list">
          <button
            v-for="feature in freqFields"
            :key="feature"
            :class="[
              'chart-feature-item',
              { active: comparison ? selecteds.includes(feature) : feature === featureVal },
            ]"
            type="button"
            @click="comparison ? $emit('toggleComparisonField', feature) : $emit('update:feature', feature)"
          >
            {{ feature }}
          </button>
        </div>
        <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
      </div>

      <div v-else-if="category === 'boxplot'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeBoxplot") }}</div>
        <p class="chart-empty chart-empty--compact">{{ boxplotCount }} {{ t("fieldsUnit") }}</p>
      </div>

      <div v-else-if="category === 'correlation'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeCorrelation") }}</div>
        <p class="chart-empty chart-empty--compact">{{ corrFieldCount }} {{ t("fieldsUnit") }}</p>
      </div>

      <div v-else-if="category === 'group_stats'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeGroupStats") }}</div>
        <div v-if="groupCatFields.length" class="chart-feature-list">
          <button
            v-for="feature in groupCatFields"
            :key="feature"
            :class="['chart-feature-item', { active: feature === featureVal }]"
            type="button"
            @click="$emit('update:feature', feature)"
          >
            {{ feature }}
          </button>
        </div>
        <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
        <div class="histogram-controls">
          <div class="histogram-control-row">
            <label class="histogram-label">{{ t("groupAggLabel") }}</label>
            <div class="chart-type-list">
              <button
                :class="['chart-type-item', { active: groupAgg === 'mean' }]"
                type="button"
                @click="$emit('update:groupAgg', 'mean')"
              >{{ t("groupAggMean") }}</button>
              <button
                :class="['chart-type-item', { active: groupAgg === 'max' }]"
                type="button"
                @click="$emit('update:groupAgg', 'max')"
              >{{ t("groupAggMax") }}</button>
              <button
                :class="['chart-type-item', { active: groupAgg === 'min' }]"
                type="button"
                @click="$emit('update:groupAgg', 'min')"
              >{{ t("groupAggMin") }}</button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="category === 'binning'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeBinning") }}</div>
        <div v-if="binningFields.length" class="chart-feature-list">
          <button
            v-for="feature in binningFields"
            :key="feature"
            :class="[
              'chart-feature-item',
              { active: comparison ? selecteds.includes(feature) : feature === featureVal },
            ]"
            type="button"
            @click="comparison ? $emit('toggleComparisonField', feature) : $emit('update:feature', feature)"
          >
            {{ feature }}
          </button>
        </div>
        <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
        <div class="histogram-controls">
          <div class="histogram-control-row">
            <label class="histogram-label">{{ t("binningMethodLabel") }}</label>
            <div class="chart-type-list">
              <button
                :class="['chart-type-item', { active: binMethod === 'equal_width' }]"
                type="button"
                @click="$emit('update:binMethod', 'equal_width')"
              >{{ t("binningEqualWidth") }}</button>
              <button
                :class="['chart-type-item', { active: binMethod === 'equal_freq' }]"
                type="button"
                @click="$emit('update:binMethod', 'equal_freq')"
              >{{ t("binningEqualFreq") }}</button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="category === 'violin'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeViolin") }}</div>
        <div v-if="violinFields.length" class="chart-feature-list">
          <button
            v-for="feature in violinFields"
            :key="feature"
            :class="[
              'chart-feature-item',
              { active: comparison ? selecteds.includes(feature) : feature === featureVal },
            ]"
            type="button"
            @click="comparison ? $emit('toggleComparisonField', feature) : $emit('update:feature', feature)"
          >{{ feature }}</button>
        </div>
        <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
      </div>

      <div v-else-if="category === 'scatter_matrix'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeScatter") }}</div>
        <div class="histogram-controls">
          <div class="histogram-control-row">
            <label class="histogram-label">{{ t("scatterXLabel") }}</label>
            <select class="chart-select" :value="scatterX" @change="$emit('update:scatterX', $event.target.value)">
              <option v-for="f in scatterFields" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <div class="histogram-control-row">
            <label class="histogram-label">{{ t("scatterYLabel") }}</label>
            <select class="chart-select" :value="scatterY" @change="$emit('update:scatterY', $event.target.value)">
              <option v-for="f in scatterFields" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
        </div>
      </div>

      <div v-else-if="category === 'missing_heatmap'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeMissingHeatmap") }}</div>
        <p class="chart-empty chart-empty--compact">
          {{ hmFieldCount }} {{ t("fieldsUnit") }} × {{ hmRowCount }} {{ t("rows") }}
        </p>
      </div>

      <div v-else-if="category === 'timeseries'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeTimeseries") }}</div>
        <div v-if="tsFields.length" class="chart-feature-list">
          <button
            v-for="feature in tsFields"
            :key="feature"
            :class="[
              'chart-feature-item',
              { active: comparison ? selecteds.includes(feature) : feature === featureVal },
            ]"
            type="button"
            @click="comparison ? $emit('toggleComparisonField', feature) : $emit('update:feature', feature)"
          >{{ feature }}</button>
        </div>
        <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
        <div class="histogram-controls">
          <div class="histogram-control-row">
            <label class="histogram-label">{{ t("timeseriesPeriodLabel") }}</label>
            <div class="chart-type-list">
              <button
                :class="['chart-type-item', { active: tsPeriod === 'daily' }]"
                type="button"
                @click="$emit('update:tsPeriod', 'daily')"
              >{{ t("timeseriesDaily") }}</button>
              <button
                :class="['chart-type-item', { active: tsPeriod === 'monthly' }]"
                type="button"
                @click="$emit('update:tsPeriod', 'monthly')"
              >{{ t("timeseriesMonthly") }}</button>
              <button
                :class="['chart-type-item', { active: tsPeriod === 'yearly' }]"
                type="button"
                @click="$emit('update:tsPeriod', 'yearly')"
              >{{ t("timeseriesYearly") }}</button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="category === 'outliers'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypeOutliers") }}</div>
        <div v-if="outlierFields.length" class="chart-feature-list">
          <button
            v-for="feature in outlierFields"
            :key="feature"
            :class="[
              'chart-feature-item',
              { active: comparison ? selecteds.includes(feature) : feature === featureVal },
            ]"
            type="button"
            @click="comparison ? $emit('toggleComparisonField', feature) : $emit('update:feature', feature)"
          >{{ feature }}</button>
        </div>
        <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
        <div v-if="featureVal" class="histogram-controls">
          <div class="histogram-control-row">
            <label class="histogram-label">{{ t("outlierIQR") }}</label>
            <span class="histogram-value">{{ outlierIqrCount }}</span>
          </div>
          <div class="histogram-control-row">
            <label class="histogram-label">{{ t("outlierZScore") }}</label>
            <span class="histogram-value">{{ outlierZscoreCount }}</span>
          </div>
        </div>
      </div>

      <div v-else-if="category === 'pareto'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartTypePareto") }}</div>
        <div v-if="paretoFields.length" class="chart-feature-list">
          <button
            v-for="feature in paretoFields"
            :key="feature"
            :class="['chart-feature-item', { active: feature === featureVal }]"
            type="button"
            @click="$emit('update:feature', feature)"
          >
            {{ feature }}
          </button>
        </div>
        <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
      </div>

      <div v-else-if="category === 'numeric_mean' || category === 'numeric_max' || category === 'numeric_min'" class="chart-type-group">
        <div class="chart-type-label">{{ t("chartType") }}</div>
        <div class="chart-type-list">
          <button
            :class="['chart-type-item', { active: chartTypeVal === 'bar' }]"
            type="button"
            @click="$emit('update:chartType', 'bar')"
          >{{ t("chartTypeBar") }}</button>
          <button
            :class="['chart-type-item', { active: chartTypeVal === 'line' }]"
            type="button"
            @click="$emit('update:chartType', 'line')"
          >{{ t("chartTypeLine") }}</button>
        </div>
      </div>

      <div v-else class="chart-type-list">
        <button
          :class="['chart-type-item', { active: chartTypeVal === 'bar' }]"
          type="button"
          @click="$emit('update:chartType', 'bar')"
        >
          {{ t("chartTypeBar") }}
        </button>
        <button
          :class="['chart-type-item', { active: chartTypeVal === 'line' }]"
          type="button"
          @click="$emit('update:chartType', 'line')"
        >
          {{ t("chartTypeLine") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from "../composables/useI18n";

defineProps({
  show: Boolean,
  analysisOptions: Array,
  category: String,
  chartTypeVal: String,
  featureVal: String,
  comparison: Boolean,
  selecteds: Array,
  histogramFields: Array,
  freqFields: Array,
  boxplotCount: Number,
  corrFieldCount: Number,
  groupCatFields: Array,
  groupAgg: String,
  binningFields: Array,
  binMethod: String,
  violinFields: Array,
  scatterFields: Array,
  scatterX: String,
  scatterY: String,
  hmFieldCount: Number,
  hmRowCount: Number,
  tsFields: Array,
  tsPeriod: String,
  outlierFields: Array,
  outlierIqrCount: Number,
  outlierZscoreCount: Number,
  paretoFields: Array,
  binCount: Number,
  normalize: Boolean,
});

defineEmits([
  "selectAnalysis", "selectChartType",
  "update:feature", "update:chartType", "toggleComparisonField",
  "update:binCount", "update:normalize",
  "update:groupAgg", "update:binMethod",
  "update:scatterX", "update:scatterY",
  "update:tsPeriod",
]);

const { t } = useI18n();
</script>
