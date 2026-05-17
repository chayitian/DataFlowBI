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
            class="chart-options-toggle"
            type="button"
            :disabled="!hasCharts"
            @click="toggleChartOptions"
          >
            <span>{{ showChartOptions ? t("collapseCharts") : t("expandCharts") }}</span>
            <span
              :class="[
                'chart-toggle-arrow',
                { open: showChartOptions },
              ]"
            >
              ▾
            </span>
          </button>
          <div class="chart-current">
            <span>{{ currentChartTitle }}</span>
          </div>
          <div v-if="hasCharts" class="chart-download-group">
            <button
              :class="['chart-download-btn', { active: showFilterPanel }]"
              type="button"
              @click="showFilterPanel = !showFilterPanel; if (showFilterPanel) initFilterInfo()"
            >
              {{ t("filterTitle") }}
            </button>
            <button
              :class="['chart-download-btn', { active: comparisonMode }]"
              type="button"
              @click="comparisonMode = !comparisonMode; selectedComparisonFields = []"
            >
              {{ t("comparisonMode") }}
            </button>
            <button
              class="chart-download-btn"
              type="button"
              title="PNG"
              @click="downloadChart('png')"
            >
              {{ t("downloadPNG") }}
            </button>
            <button
              class="chart-download-btn"
              type="button"
              title="SVG"
              @click="downloadChart('svg')"
            >
              {{ t("downloadSVG") }}
            </button>
          </div>
        </div>
        <div v-if="showFilterPanel && preview?.filter_info" class="filter-panel">
          <div class="filter-header">
            <span class="filter-title">{{ t("filterTitle") }}</span>
            <div class="chart-download-group">
              <button class="chart-download-btn" type="button" @click="applyFilter">{{ t("filterApply") }}</button>
              <button class="chart-download-btn" type="button" @click="resetFilter">{{ t("filterReset") }}</button>
            </div>
          </div>
          <div class="filter-body">
            <div v-for="(meta, field) in preview.filter_info" :key="field" class="filter-field">
              <div class="filter-field-label">{{ field }} <span class="filter-field-type">({{ meta.dtype }})</span></div>
              <div v-if="meta.min != null && meta.max != null" class="filter-range-row">
                <input
                  type="range"
                  class="histogram-slider filter-slider"
                  :min="meta.min"
                  :max="meta.max"
                  :value="(filterNumericRanges[field] || [meta.min, meta.max])[0]"
                  @input="filterNumericRanges[field] = [Number($event.target.value), (filterNumericRanges[field] || [meta.min, meta.max])[1]]"
                />
                <input
                  type="range"
                  class="histogram-slider filter-slider"
                  :min="meta.min"
                  :max="meta.max"
                  :value="(filterNumericRanges[field] || [meta.min, meta.max])[1]"
                  @input="filterNumericRanges[field] = [(filterNumericRanges[field] || [meta.min, meta.max])[0], Number($event.target.value)]"
                />
                <span class="filter-range-label">
                  {{ formatNumber((filterNumericRanges[field] || [meta.min, meta.max])[0]) }} — {{ formatNumber((filterNumericRanges[field] || [meta.min, meta.max])[1]) }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="showChartOptions && hasCharts" class="chart-options">
          <div class="chart-options-left">
            <div class="chart-options-title">{{ t("analysisCategory") }}</div>
            <button
              v-for="option in analysisOptions"
              :key="option.key"
              :class="[
                'chart-option-item',
                { active: option.key === chartCategory },
              ]"
              type="button"
              @click="selectAnalysis(option.key)"
            >
              <span>{{ option.label }}</span>
              <span
                :class="[
                  'chart-option-arrow',
                  { open: option.key === chartCategory },
                ]"
              >
                ▾
              </span>
            </button>
          </div>
          <div class="chart-options-right">
            <div class="chart-options-title">{{ t("chartType") }}</div>
            <div v-if="showHistogramSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeHistogram") }}</div>
              <div v-if="histogramFeatures.length" class="chart-feature-list">
                <button
                  v-for="feature in histogramFeatures"
                  :key="feature"
                  :class="[
                    'chart-feature-item',
                    { active: comparisonMode ? selectedComparisonFields.includes(feature) : feature === chartFeature },
                  ]"
                  type="button"
                  @click="comparisonMode ? toggleComparisonField(feature) : selectFeature(feature)"
                >
                  {{ feature }}
                </button>
              </div>
              <p v-else class="chart-empty chart-empty--compact">
                {{ t("chartNoHistogram") }}
              </p>
              <div class="histogram-controls">
                <div class="histogram-control-row">
                  <label class="histogram-label">{{ t("histogramBins") }}</label>
                  <input
                    type="range"
                    class="histogram-slider"
                    v-model.number="histogramBinCount"
                    min="2"
                    max="50"
                  />
                  <span class="histogram-value">{{ histogramBinCount }}</span>
                </div>
                <label class="checkbox histogram-checkbox">
                  <input type="checkbox" v-model="histogramNormalize" />
                  <span>{{ t("histogramNormalize") }}</span>
                </label>
              </div>
            </div>
            <div v-else-if="showFrequencySelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeFrequency") }}</div>
              <div v-if="frequencyFields.length" class="chart-feature-list">
                <button
                  v-for="feature in frequencyFields"
                  :key="feature"
                  :class="[
                    'chart-feature-item',
                    { active: comparisonMode ? selectedComparisonFields.includes(feature) : feature === chartFeature },
                  ]"
                  type="button"
                  @click="comparisonMode ? toggleComparisonField(feature) : selectFeature(feature)"
                >
                  {{ feature }}
                </button>
              </div>
              <p v-else class="chart-empty chart-empty--compact">
                {{ t("chartNoHistogram") }}
              </p>
            </div>
            <div v-else-if="showBoxplotSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeBoxplot") }}</div>
              <p class="chart-empty chart-empty--compact">{{ boxplotFields.length }} {{ t("fieldsUnit") }}</p>
            </div>
            <div v-else-if="showCorrelationSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeCorrelation") }}</div>
              <p class="chart-empty chart-empty--compact">
                {{ reportData?.correlation?.fields?.length || 0 }} {{ t("fieldsUnit") }}
              </p>
            </div>
            <div v-else-if="showGroupStatsSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeGroupStats") }}</div>
              <div v-if="groupCategoricalFields.length" class="chart-feature-list">
                <button
                  v-for="feature in groupCategoricalFields"
                  :key="feature"
                  :class="[
                    'chart-feature-item',
                    { active: feature === chartFeature },
                  ]"
                  type="button"
                  @click="selectFeature(feature)"
                >
                  {{ feature }}
                </button>
              </div>
              <p v-else class="chart-empty chart-empty--compact">
                {{ t("chartNoHistogram") }}
              </p>
              <div class="histogram-controls">
                <div class="histogram-control-row">
                  <label class="histogram-label">{{ t("groupAggLabel") }}</label>
                  <div class="chart-type-list">
                    <button
                      :class="['chart-type-item', { active: groupAggregation === 'mean' }]"
                      type="button"
                      @click="groupAggregation = 'mean'"
                    >{{ t("groupAggMean") }}</button>
                    <button
                      :class="['chart-type-item', { active: groupAggregation === 'max' }]"
                      type="button"
                      @click="groupAggregation = 'max'"
                    >{{ t("groupAggMax") }}</button>
                    <button
                      :class="['chart-type-item', { active: groupAggregation === 'min' }]"
                      type="button"
                      @click="groupAggregation = 'min'"
                    >{{ t("groupAggMin") }}</button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="showBinningSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeBinning") }}</div>
              <div v-if="binningFields.length" class="chart-feature-list">
                <button
                  v-for="feature in binningFields"
                  :key="feature"
                  :class="[
                    'chart-feature-item',
                    { active: comparisonMode ? selectedComparisonFields.includes(feature) : feature === chartFeature },
                  ]"
                  type="button"
                  @click="comparisonMode ? toggleComparisonField(feature) : selectFeature(feature)"
                >
                  {{ feature }}
                </button>
              </div>
              <p v-else class="chart-empty chart-empty--compact">
                {{ t("chartNoHistogram") }}
              </p>
              <div class="histogram-controls">
                <div class="histogram-control-row">
                  <label class="histogram-label">{{ t("binningMethodLabel") }}</label>
                  <div class="chart-type-list">
                    <button
                      :class="['chart-type-item', { active: binningMethod === 'equal_width' }]"
                      type="button"
                      @click="binningMethod = 'equal_width'"
                    >{{ t("binningEqualWidth") }}</button>
                    <button
                      :class="['chart-type-item', { active: binningMethod === 'equal_freq' }]"
                      type="button"
                      @click="binningMethod = 'equal_freq'"
                    >{{ t("binningEqualFreq") }}</button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="showViolinSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeViolin") }}</div>
              <div v-if="violinFields.length" class="chart-feature-list">
                <button
                  v-for="feature in violinFields"
                  :key="feature"
                  :class="[
                    'chart-feature-item',
                    { active: comparisonMode ? selectedComparisonFields.includes(feature) : feature === chartFeature },
                  ]"
                  type="button"
                  @click="comparisonMode ? toggleComparisonField(feature) : selectFeature(feature)"
                >{{ feature }}</button>
              </div>
              <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
            </div>
            <div v-else-if="showScatterSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeScatter") }}</div>
              <div class="histogram-controls">
                <div class="histogram-control-row">
                  <label class="histogram-label">{{ t("scatterXLabel") }}</label>
                  <select class="chart-select" v-model="scatterXField">
                    <option v-for="f in scatterFields" :key="f" :value="f">{{ f }}</option>
                  </select>
                </div>
                <div class="histogram-control-row">
                  <label class="histogram-label">{{ t("scatterYLabel") }}</label>
                  <select class="chart-select" v-model="scatterYField">
                    <option v-for="f in scatterFields" :key="f" :value="f">{{ f }}</option>
                  </select>
                </div>
              </div>
            </div>
            <div v-else-if="showMissingHeatmapSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeMissingHeatmap") }}</div>
              <p class="chart-empty chart-empty--compact">
                {{ reportData?.missing_heatmap?.fields?.length || 0 }} {{ t("fieldsUnit") }} × {{ reportData?.missing_heatmap?.rows || 0 }} {{ t("rows") }}
              </p>
            </div>
            <div v-else-if="showTimeseriesSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeTimeseries") }}</div>
              <div v-if="timeseriesFields.length" class="chart-feature-list">
                <button
                  v-for="feature in timeseriesFields"
                  :key="feature"
                  :class="[
                    'chart-feature-item',
                    { active: comparisonMode ? selectedComparisonFields.includes(feature) : feature === chartFeature },
                  ]"
                  type="button"
                  @click="comparisonMode ? toggleComparisonField(feature) : selectFeature(feature)"
                >{{ feature }}</button>
              </div>
              <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
              <div class="histogram-controls">
                <div class="histogram-control-row">
                  <label class="histogram-label">{{ t("timeseriesPeriodLabel") }}</label>
                  <div class="chart-type-list">
                    <button
                      :class="['chart-type-item', { active: timeseriesPeriod === 'daily' }]"
                      type="button"
                      @click="timeseriesPeriod = 'daily'"
                    >{{ t("timeseriesDaily") }}</button>
                    <button
                      :class="['chart-type-item', { active: timeseriesPeriod === 'monthly' }]"
                      type="button"
                      @click="timeseriesPeriod = 'monthly'"
                    >{{ t("timeseriesMonthly") }}</button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="showOutliersSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypeOutliers") }}</div>
              <div v-if="outlierFields.length" class="chart-feature-list">
                <button
                  v-for="feature in outlierFields"
                  :key="feature"
                  :class="[
                    'chart-feature-item',
                    { active: comparisonMode ? selectedComparisonFields.includes(feature) : feature === chartFeature },
                  ]"
                  type="button"
                  @click="comparisonMode ? toggleComparisonField(feature) : selectFeature(feature)"
                >{{ feature }}</button>
              </div>
              <p v-else class="chart-empty chart-empty--compact">{{ t("chartNoHistogram") }}</p>
              <div class="histogram-controls" v-if="chartFeature">
                <div class="histogram-control-row">
                  <label class="histogram-label">{{ t("outlierIQR") }}</label>
                  <span class="histogram-value">{{ reportData?.outliers?.[chartFeature]?.iqr?.count || 0 }}</span>
                </div>
                <div class="histogram-control-row">
                  <label class="histogram-label">{{ t("outlierZScore") }}</label>
                  <span class="histogram-value">{{ reportData?.outliers?.[chartFeature]?.zscore?.count || 0 }}</span>
                </div>
              </div>
            </div>
            <div v-else-if="showParetoSelector" class="chart-type-group">
              <div class="chart-type-label">{{ t("chartTypePareto") }}</div>
              <div v-if="paretoFields.length" class="chart-feature-list">
                <button
                  v-for="feature in paretoFields"
                  :key="feature"
                  :class="[
                    'chart-feature-item',
                    { active: feature === chartFeature },
                  ]"
                  type="button"
                  @click="selectFeature(feature)"
                >
                  {{ feature }}
                </button>
              </div>
              <p v-else class="chart-empty chart-empty--compact">
                {{ t("chartNoHistogram") }}
              </p>
            </div>
            <div v-else class="chart-type-list">
              <button
                :class="[
                  'chart-type-item',
                  { active: chartType === 'bar' },
                ]"
                type="button"
                @click="selectChartType('bar')"
              >
                {{ t("chartTypeBar") }}
              </button>
              <button
                :class="[
                  'chart-type-item',
                  { active: chartType === 'line' },
                ]"
                type="button"
                @click="selectChartType('line')"
              >
                {{ t("chartTypeLine") }}
              </button>
            </div>
          </div>
        </div>
        <div ref="chartEl" class="chart-canvas"></div>
        <p v-if="!hasCharts || !hasChartData" class="chart-empty">{{ t("chartEmpty") }}</p>
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
                v-model="selection.charts.feature_distribution"
              />
              <span>{{ t("analysisFeatureDistribution") }}</span>
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
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.violin"
              />
              <span>{{ t("selectionViolin") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.scatter_matrix"
              />
              <span>{{ t("selectionScatter") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.missing_heatmap"
              />
              <span>{{ t("selectionMissingHeatmap") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.timeseries"
              />
              <span>{{ t("selectionTimeseries") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.outliers"
              />
              <span>{{ t("selectionOutliers") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.boxplot"
              />
              <span>{{ t("selectionBoxplot") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.correlation"
              />
              <span>{{ t("selectionCorrelation") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.group_stats"
              />
              <span>{{ t("selectionGroupStats") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.binning"
              />
              <span>{{ t("selectionBinning") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.frequency"
              />
              <span>{{ t("selectionFrequency") }}</span>
            </label>
            <label class="checkbox">
              <input
                type="checkbox"
                v-model="selection.charts.pareto"
              />
              <span>{{ t("selectionPareto") }}</span>
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
import { filterData as filterApi, rebinHistogram as rebinApi, uploadDataset } from "./api/upload";

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
    feature_distribution: true,
    numeric_mean: false,
    numeric_max: false,
    numeric_min: false,
    dtype_distribution: true,
    frequency: false,
    pareto: false,
    boxplot: false,
    correlation: false,
    group_stats: false,
    binning: false,
    violin: false,
    scatter_matrix: false,
    missing_heatmap: false,
    timeseries: false,
    outliers: false,
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
    chartSubtitle: "展开可视化选项，左侧选类别，右侧选图形类型。",
    chartEmpty: "暂无可视化数据，请先上传文件。",
    analysisCategory: "分析类别",
    chartType: "图形类别",
    analysisMissingRate: "缺失率",
    analysisFeatureDistribution: "特征分布",
    analysisNumericMean: "均值",
    analysisNumericMax: "最大值",
    analysisNumericMin: "最小值",
    analysisTypeDistribution: "字段类型分布",
    analysisFrequency: "频次分布",
    analysisPareto: "贡献度(Pareto)",
    analysisBoxplot: "箱线图",
    analysisCorrelation: "相关性热力图",
    analysisGroupStats: "分组统计",
    analysisBinning: "分箱统计",
    analysisViolin: "小提琴图",
    analysisScatter: "散点图",
    analysisMissingHeatmap: "缺失值热力图",
    analysisTimeseries: "时间序列",
    analysisOutliers: "离群值检测",
    chartTypeBar: "柱状图",
    chartTypeLine: "折线图",
    chartTypeHistogram: "直方图 + 分布图",
    chartTypeFrequency: "分类频次 Top N",
    chartTypePareto: "Pareto 图",
    downloadPNG: "下载 PNG",
    downloadSVG: "下载 SVG",
    chartTypeBoxplot: "箱线图",
    chartTypeCorrelation: "相关性矩阵",
    chartTypeGroupStats: "分组聚合",
    chartTypeBinning: "分箱方式",
    chartTypeViolin: "密度分布",
    chartTypeScatter: "X/Y 轴",
    chartTypeMissingHeatmap: "缺失矩阵",
    chartTypeTimeseries: "聚合周期",
    chartTypeOutliers: "异常值检测",
    histogramBins: "分箱数",
    histogramNormalize: "标准化",
    scatterXLabel: "X 轴字段",
    scatterYLabel: "Y 轴字段",
    timeseriesPeriodLabel: "聚合周期",
    timeseriesDaily: "按日",
    timeseriesMonthly: "按月",
    comparisonMode: "对比模式",
    comparisonModeOff: "关闭",
    comparisonModeOn: "开启",
    filterTitle: "数据筛选",
    filterApply: "应用筛选",
    filterReset: "重置",
    filterNoData: "暂无字段信息",
    outlierMethodLabel: "检测方法",
    outlierIQR: "IQR",
    outlierZScore: "Z-Score",
    outlierSampleLabel: "样本值",
    groupAggLabel: "聚合方式",
    groupAggMean: "均值",
    groupAggMax: "最大值",
    groupAggMin: "最小值",
    binningMethodLabel: "分箱方式",
    binningEqualWidth: "等距",
    binningEqualFreq: "等频",
    selectionBoxplot: "箱线图",
    selectionCorrelation: "相关性热力图",
    selectionGroupStats: "分组统计",
    selectionBinning: "分箱统计",
    selectionViolin: "小提琴图",
    selectionScatter: "散点图",
    selectionMissingHeatmap: "缺失值热力图",
    selectionTimeseries: "时间序列趋势",
    selectionOutliers: "离群值检测",
    chartNoHistogram: "暂无可用数值字段。",
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
    selectionChartsHint: "勾选需要展示的分析类别",
    selectionFrequency: "频次分布",
    selectionPareto: "Pareto 贡献度",
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
    chartSubtitle: "Expand options, pick a category on the left and a chart type on the right.",
    chartEmpty: "No chart data available. Please upload a file.",
    analysisCategory: "Analysis category",
    chartType: "Chart type",
    analysisMissingRate: "Missing rate",
    analysisFeatureDistribution: "Feature distribution",
    analysisNumericMean: "Mean",
    analysisNumericMax: "Max",
    analysisNumericMin: "Min",
    analysisTypeDistribution: "Type distribution",
    analysisFrequency: "Frequency",
    analysisPareto: "Pareto",
    analysisBoxplot: "Boxplot",
    analysisCorrelation: "Correlation Heatmap",
    analysisGroupStats: "Group Stats",
    analysisBinning: "Binning",
    analysisViolin: "Violin",
    analysisScatter: "Scatter",
    analysisMissingHeatmap: "Missing Heatmap",
    analysisTimeseries: "Time Series",
    analysisOutliers: "Outlier Detection",
    scatterXLabel: "X Field",
    scatterYLabel: "Y Field",
    timeseriesPeriodLabel: "Period",
    timeseriesDaily: "Daily",
    timeseriesMonthly: "Monthly",
    comparisonMode: "Compare",
    comparisonModeOff: "Off",
    comparisonModeOn: "On",
    filterTitle: "Data Filter",
    filterApply: "Apply",
    filterReset: "Reset",
    filterNoData: "No field info",
    outlierMethodLabel: "Method",
    outlierIQR: "IQR",
    outlierZScore: "Z-Score",
    outlierSampleLabel: "Samples",
    chartTypeBar: "Bar",
    chartTypeLine: "Line",
    chartTypeHistogram: "Histogram + Distribution",
    chartTypeFrequency: "Categorical Top N",
    chartTypePareto: "Pareto",
    downloadPNG: "Download PNG",
    downloadSVG: "Download SVG",
    chartTypeBoxplot: "Boxplot",
    chartTypeCorrelation: "Correlation matrix",
    chartTypeGroupStats: "Group aggregation",
    chartTypeBinning: "Binning method",
    chartTypeViolin: "Density",
    chartTypeScatter: "X/Y axes",
    chartTypeMissingHeatmap: "Missing matrix",
    chartTypeTimeseries: "Aggregation",
    chartTypeOutliers: "Outlier detection",
    histogramBins: "Bins",
    histogramNormalize: "Normalize",
    groupAggLabel: "Aggregation",
    groupAggMean: "Mean",
    groupAggMax: "Max",
    groupAggMin: "Min",
    binningMethodLabel: "Method",
    binningEqualWidth: "Equal width",
    binningEqualFreq: "Equal freq",
    selectionBoxplot: "Boxplot",
    selectionCorrelation: "Correlation heatmap",
    selectionGroupStats: "Group statistics",
    selectionBinning: "Binning",
    selectionViolin: "Violin plot",
    selectionScatter: "Scatter plot",
    selectionMissingHeatmap: "Missing heatmap",
    selectionTimeseries: "Time series",
    selectionOutliers: "Outlier detection",
    chartNoHistogram: "No numeric fields available.",
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
    selectionChartsHint: "Select analysis categories to display",
    selectionFrequency: "Frequency distribution",
    selectionPareto: "Pareto chart",
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

const chartCategory = ref(null);
const chartType = ref("bar");
const chartFeature = ref(null);
const showChartOptions = ref(false);
const chartEl = ref(null);
const chartInstance = ref(null);
const savedName = ref("");
const histogramBinCount = ref(10);
const histogramNormalize = ref(false);
const rebinData = ref(null);
const histogramDefaultBinCount = 8;
const groupAggregation = ref("mean");
const binningMethod = ref("equal_width");
const scatterXField = ref("");
const scatterYField = ref("");
const timeseriesPeriod = ref("daily");
const comparisonMode = ref(false);
const selectedComparisonFields = ref([]);
const showFilterPanel = ref(false);
const filterNumericRanges = ref({});
const filterCategoricalValues = ref({});
const filteredData = ref(null);

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
const analysisOptions = computed(() => {
  const charts = appliedSelection.value?.charts || {};
  const options = [
    { key: "missing_rate", label: t("analysisMissingRate") },
    { key: "feature_distribution", label: t("analysisFeatureDistribution") },
    { key: "violin", label: t("analysisViolin") },
    { key: "scatter_matrix", label: t("analysisScatter") },
    { key: "missing_heatmap", label: t("analysisMissingHeatmap") },
    { key: "timeseries", label: t("analysisTimeseries") },
    { key: "outliers", label: t("analysisOutliers") },
    { key: "boxplot", label: t("analysisBoxplot") },
    { key: "correlation", label: t("analysisCorrelation") },
    { key: "group_stats", label: t("analysisGroupStats") },
    { key: "binning", label: t("analysisBinning") },
    { key: "frequency", label: t("analysisFrequency") },
    { key: "pareto", label: t("analysisPareto") },
    { key: "dtype_distribution", label: t("analysisTypeDistribution") },
    { key: "numeric_mean", label: t("analysisNumericMean") },
    { key: "numeric_max", label: t("analysisNumericMax") },
    { key: "numeric_min", label: t("analysisNumericMin") },
  ];

  return options.filter((option) => charts[option.key]);
});

const histogramFeatures = computed(() =>
  Object.keys(reportData.value?.histograms || {})
);
const frequencyFields = computed(() =>
  Object.keys(reportData.value?.frequencies || {})
);
const paretoFields = computed(() =>
  Object.keys(reportData.value?.pareto || {})
);
const showHistogramSelector = computed(
  () => chartCategory.value === "feature_distribution"
);
const showFrequencySelector = computed(
  () => chartCategory.value === "frequency"
);
const showParetoSelector = computed(
  () => chartCategory.value === "pareto"
);
const boxplotFields = computed(() =>
  Object.keys(reportData.value?.boxplot || {})
);
const groupCategoricalFields = computed(() =>
  reportData.value?.group_stats?.categorical_fields || []
);
const binningFields = computed(() =>
  Object.keys(reportData.value?.binning || {})
);
const showBoxplotSelector = computed(
  () => chartCategory.value === "boxplot"
);
const showCorrelationSelector = computed(
  () => chartCategory.value === "correlation"
);
const showGroupStatsSelector = computed(
  () => chartCategory.value === "group_stats"
);
const showBinningSelector = computed(
  () => chartCategory.value === "binning"
);
const violinFields = computed(() =>
  Object.keys(reportData.value?.violin || {})
);
const scatterFields = computed(() =>
  reportData.value?.scatter_matrix?.fields || []
);
const timeseriesFields = computed(() =>
  Object.keys(reportData.value?.timeseries || {})
);
const outlierFields = computed(() =>
  Object.keys(reportData.value?.outliers || {})
);
const showViolinSelector = computed(
  () => chartCategory.value === "violin"
);
const showScatterSelector = computed(
  () => chartCategory.value === "scatter_matrix"
);
const showMissingHeatmapSelector = computed(
  () => chartCategory.value === "missing_heatmap"
);
const showTimeseriesSelector = computed(
  () => chartCategory.value === "timeseries"
);
const showOutliersSelector = computed(
  () => chartCategory.value === "outliers"
);

const hasCharts = computed(
  () => showChartSection.value && analysisOptions.value.length > 0
);

const currentChartTitle = computed(() => {
  if (!hasCharts.value) {
    return t("chartEmpty");
  }

  const active = analysisOptions.value.find(
    (option) => option.key === chartCategory.value
  );
  const label = active?.label || "";

  if (chartCategory.value === "feature_distribution") {
    const feature = chartFeature.value ? ` · ${chartFeature.value}` : "";
    return `${label} · ${t("chartTypeHistogram")}${feature}`;
  }

  if (chartCategory.value === "frequency") {
    const feature = chartFeature.value ? ` · ${chartFeature.value}` : "";
    return `${label}${feature}`;
  }

  if (chartCategory.value === "violin") {
    const feature = chartFeature.value ? ` · ${chartFeature.value}` : "";
    return `${label}${feature}`;
  }

  if (chartCategory.value === "scatter_matrix") {
    const xf = scatterXField.value || "?";
    const yf = scatterYField.value || "?";
    return `${label} · ${xf} × ${yf}`;
  }

  if (chartCategory.value === "missing_heatmap") {
    return `${label} · ${t("chartTypeMissingHeatmap")}`;
  }

  if (chartCategory.value === "timeseries") {
    const feature = chartFeature.value ? ` · ${chartFeature.value}` : "";
    const period = timeseriesPeriod.value === "daily" ? t("timeseriesDaily") : t("timeseriesMonthly");
    return `${label}${feature} · ${period}`;
  }

  if (chartCategory.value === "outliers") {
    const feature = chartFeature.value ? ` · ${chartFeature.value}` : "";
    return `${label}${feature}`;
  }

  if (chartCategory.value === "boxplot") {
    return `${label} · ${t("chartTypeBoxplot")}`;
  }

  if (chartCategory.value === "correlation") {
    return `${label} · ${t("chartTypeCorrelation")}`;
  }

  if (chartCategory.value === "group_stats") {
    const feature = chartFeature.value ? ` · ${chartFeature.value}` : "";
    const agg = t("groupAgg" + groupAggregation.value.charAt(0).toUpperCase() + groupAggregation.value.slice(1));
    return `${label}${feature} · ${agg}`;
  }

  if (chartCategory.value === "binning") {
    const feature = chartFeature.value ? ` · ${chartFeature.value}` : "";
    const method = binningMethod.value === "equal_width" ? t("binningEqualWidth") : t("binningEqualFreq");
    return `${label}${feature} · ${method}`;
  }

  if (chartCategory.value === "pareto") {
    const feature = chartFeature.value ? ` · ${chartFeature.value}` : "";
    return `${label}${feature}`;
  }

  const typeLabel =
    chartType.value === "line" ? t("chartTypeLine") : t("chartTypeBar");
  return `${label} · ${typeLabel}`;
});

const activeReport = computed(() =>
  filteredData.value?.report || reportData.value
);

const chartOption = computed(() => {
  rebinData.value;
  groupAggregation.value;
  binningMethod.value;
  scatterXField.value;
  scatterYField.value;
  timeseriesPeriod.value;
  comparisonMode.value;
  selectedComparisonFields.value;
  return buildChartOption(
    activeReport.value,
    chartCategory.value,
    chartType.value,
    chartFeature.value
  );
});
const hasChartData = computed(() => Boolean(chartOption.value));

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

const buildHistogramOption = (report, feature) => {
  const histogram = report?.histograms?.[feature];
  if (!histogram) {
    return null;
  }

  const bins = histogram.bins || [];
  const counts = histogram.counts || [];
  if (!bins.length || !counts.length) {
    return null;
  }

  const labels = bins.slice(0, -1).map((value, index) => {
    const start = Number(value);
    const end = Number(bins[index + 1]);

    if (Number.isNaN(start) || Number.isNaN(end)) {
      return `Bin ${index + 1}`;
    }

    return `${start.toFixed(2)} - ${end.toFixed(2)}`;
  });

  return {
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
  };
};

const buildNumericOption = (report, metricKey, type) => {
  const summary = report?.numeric_summary || {};
  const entries = Object.entries(summary);
  if (!entries.length) {
    return null;
  }

  const limited = entries.slice(0, MAX_CHART_FIELDS);
  const categories = limited.map(([field]) => field);
  const values = limited.map(([, stats]) => toNumber(stats?.[metricKey]));

  return type === "line"
    ? buildLineOption(categories, values, "", LINE_COLOR)
    : buildBarOption(categories, values, "", BAR_COLOR);
};

const buildMissingRateOption = (report, type) => {
  const entries = Object.entries(report?.missing_rate || {});
  if (!entries.length) {
    return null;
  }

  const limited = entries.slice(0, MAX_CHART_FIELDS);
  const categories = limited.map(([field]) => field);
  const values = limited.map(([, value]) => toNumber(value) * 100);

  return type === "line"
    ? buildLineOption(categories, values, "%", LINE_COLOR)
    : buildBarOption(categories, values, "%", BAR_COLOR);
};

const buildTypeDistributionOption = (report, type) => {
  const dtypes = report?.dtypes || {};
  const counts = {};

  Object.values(dtypes).forEach((dtype) => {
    counts[dtype] = (counts[dtype] || 0) + 1;
  });

  const entries = Object.entries(counts);
  if (!entries.length) {
    return null;
  }

  const labels = entries.map(([dtype]) => dtype);
  const values = entries.map(([, count]) => count);

  return type === "line"
    ? buildLineOption(labels, values, "", LINE_COLOR)
    : buildBarOption(labels, values, "", BAR_COLOR);
};

const buildFrequencyOption = (report, field, type) => {
  const data = report?.frequencies?.[field];
  if (!data?.length) return null;
  const categories = data.map((d) => String(d.value));
  const values = data.map((d) => d.count);
  return type === "line"
    ? buildLineOption(categories, values, "", LINE_COLOR)
    : buildBarOption(categories, values, "", BAR_COLOR);
};

const buildParetoOption = (report, field) => {
  const data = report?.pareto?.[field];
  if (!data?.length) return null;
  const categories = data.map((_, i) => `#${i + 1}`);
  const values = data.map((d) => d.value);
  const cumPcts = data.map((d) => Number((d.cum_pct * 100).toFixed(1)));

  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 30, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: categories, axisLabel: { rotate: 25 } },
    yAxis: [
      { type: "value", name: t("analysisPareto") },
      { type: "value", name: "%", max: 100 },
    ],
    series: [
      {
        type: "bar",
        data: values,
        itemStyle: { color: BAR_COLOR },
        barMaxWidth: 36,
      },
      {
        type: "line",
        data: cumPcts,
        smooth: true,
        yAxisIndex: 1,
        symbol: "circle",
        symbolSize: 8,
        lineStyle: { color: LINE_COLOR, width: 3 },
        itemStyle: { color: LINE_COLOR },
        areaStyle: { color: "rgba(29, 161, 167, 0.15)" },
      },
    ],
  };
};

const buildBoxplotOption = (report) => {
  const data = report?.boxplot || {};
  const entries = Object.entries(data).slice(0, MAX_CHART_FIELDS);
  if (!entries.length) return null;

  const categories = entries.map(([field]) => field);
  const boxData = entries.map(([, stats]) => [
    stats.min, stats.q1, stats.median, stats.q3, stats.max,
  ]);
  const outliers = entries.map(([, stats]) => stats.outliers || []);

  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: categories, axisLabel: { rotate: 25 } },
    yAxis: { type: "value" },
    series: [
      {
        name: "boxplot",
        type: "boxplot",
        data: boxData,
        itemStyle: { color: BAR_COLOR },
        tooltip: {
          formatter: (params) => {
            const d = data[params.name];
            if (!d) return params.name;
            return `${params.name}<br/>Min: ${d.min}<br/>Q1: ${d.q1}<br/>Median: ${d.median}<br/>Q3: ${d.q3}<br/>Max: ${d.max}`;
          },
        },
      },
      {
        name: "outliers",
        type: "scatter",
        data: outliers.flatMap((list, i) =>
          list.map((v) => [i, v])
        ),
        symbolSize: 6,
        itemStyle: { color: "#e74c3c" },
      },
    ],
  };
};

const buildCorrelationOption = (report) => {
  const corr = report?.correlation;
  if (!corr || !corr.fields?.length || !corr.matrix?.length) return null;

  const fields = corr.fields;
  const matrix = corr.matrix;
  const data = [];
  for (let i = 0; i < fields.length; i++) {
    for (let j = 0; j < fields.length; j++) {
      const val = matrix[i]?.[j];
      if (val !== null && val !== undefined) {
        data.push([i, j, val]);
      }
    }
  }

  return {
    tooltip: {
      formatter: (params) => {
        const x = fields[params.value[0]];
        const y = fields[params.value[1]];
        return `${x} × ${y}<br/>${params.value[2].toFixed(4)}`;
      },
    },
    grid: { left: 60, right: 20, top: 20, bottom: 60 },
    xAxis: {
      type: "category",
      data: fields,
      axisLabel: { rotate: 45 },
      splitArea: { show: true },
    },
    yAxis: {
      type: "category",
      data: fields,
      axisLabel: { rotate: 0 },
      splitArea: { show: true },
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: "vertical",
      right: 0,
      top: 20,
      inRange: { color: ["#1da1a7", "#ffffff", "#f26b38"] },
    },
    series: [
      {
        type: "heatmap",
        data,
        label: {
          show: fields.length <= 8,
          formatter: (params) => params.value[2].toFixed(2),
        },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.3)" },
        },
      },
    ],
  };
};

const buildGroupStatsOption = (report, groupField, agg) => {
  const gs = report?.group_stats;
  if (!gs || !gs.data?.[groupField]) return null;

  const groupData = gs.data[groupField];
  const groups = Object.keys(groupData);
  const numericFields = gs.numeric_fields || [];

  const allStats = {};
  for (const gf of groups) {
    for (const nf of numericFields) {
      const s = groupData[gf]?.[nf];
      if (s && s[agg] !== null && s[agg] !== undefined) {
        if (!allStats[nf]) allStats[nf] = {};
        allStats[nf][gf] = s[agg];
      }
    }
  }

  const nfEntries = Object.entries(allStats).slice(0, MAX_CHART_FIELDS);
  if (!nfEntries.length) return null;

  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: groups, axisLabel: { rotate: 25 } },
    yAxis: { type: "value" },
    series: nfEntries.map(([field, groupVals], i) => ({
      name: field,
      type: "bar",
      data: groups.map((g) => groupVals[g] ?? null),
      barMaxWidth: 24,
      itemStyle: {
        color: i % 2 === 0 ? BAR_COLOR : LINE_COLOR,
      },
    })),
  };
};

const buildBinningOption = (report, field, method) => {
  const binData = report?.binning?.[field]?.[method];
  if (!binData || !binData.bins?.length) return null;

  const labels = binData.bins.slice(0, -1).map((start, idx) => {
    const end = binData.bins[idx + 1];
    return `${Number(start).toFixed(2)} - ${Number(end).toFixed(2)}`;
  });

  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: labels, axisLabel: { rotate: 25 } },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: binData.counts,
        itemStyle: { color: BAR_COLOR },
        barMaxWidth: 36,
      },
    ],
  };
};

const buildViolinOption = (report, field) => {
  const v = report?.violin?.[field];
  if (!v || !v.density_x?.length) return null;

  const left = v.density_x.map((x, i) => [-v.density_y[i], x]);
  const right = v.density_x.map((x, i) => [v.density_y[i], x]);

  return {
    tooltip: {
      trigger: "axis",
      formatter: (params) => {
        const item = params[0];
        return `${field}<br/>${item.name}`;
      },
    },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: "value", name: t("chartTypeViolin") },
    yAxis: { type: "value", name: t("fieldLabel") },
    series: [
      {
        type: "scatter",
        data: left,
        symbol: "none",
        lineStyle: { color: BAR_COLOR, width: 0 },
        areaStyle: { color: BAR_COLOR, opacity: 0.3 },
        step: "end",
      },
      {
        type: "scatter",
        data: right,
        symbol: "none",
        lineStyle: { color: BAR_COLOR, width: 0 },
        areaStyle: { color: BAR_COLOR, opacity: 0.3 },
        step: "start",
      },
      {
        type: "line",
        data: left,
        smooth: true,
        symbol: "none",
        lineStyle: { color: BAR_COLOR, width: 2 },
      },
      {
        type: "line",
        data: right,
        smooth: true,
        symbol: "none",
        lineStyle: { color: BAR_COLOR, width: 2 },
      },
    ],
  };
};

const buildScatterOption = (report, xField, yField) => {
  const data = report?.scatter_matrix?.data;
  if (!data?.length || !xField || !yField) return null;

  const points = data
    .filter((d) => d[xField] != null && d[yField] != null)
    .slice(0, 1000)
    .map((d) => [Number(d[xField]), Number(d[yField])]);

  if (!points.length) return null;

  return {
    tooltip: {
      formatter: (params) => `${xField}: ${params.value[0]}<br/>${yField}: ${params.value[1]}`,
    },
    grid: { left: 50, right: 20, top: 20, bottom: 50 },
    xAxis: { type: "value", name: xField },
    yAxis: { type: "value", name: yField },
    series: [
      {
        type: "scatter",
        data: points,
        symbolSize: 6,
        itemStyle: { color: BAR_COLOR, opacity: 0.6 },
      },
    ],
  };
};

const buildMissingHeatmapOption = (report) => {
  const hm = report?.missing_heatmap;
  if (!hm || !hm.data?.length) return null;

  const data = [];
  for (let r = 0; r < hm.data.length; r++) {
    for (let c = 0; c < hm.data[r].length; c++) {
      if (hm.data[r][c]) {
        data.push([c, r, 1]);
      }
    }
  }

  const fields = hm.fields || [];
  const nRows = hm.rows || hm.data.length;

  return {
    tooltip: {
      formatter: (params) => {
        const f = fields[params.value[0]] || "?";
        return `${t("fieldLabel")}: ${f}<br/>${t("rows")}: ${params.value[1] + 1}`;
      },
    },
    grid: { left: 60, right: 30, top: 20, bottom: 60 },
    xAxis: {
      type: "category",
      data: fields,
      axisLabel: { rotate: 45 },
      splitArea: { show: true },
    },
    yAxis: {
      type: "category",
      data: Array.from({ length: nRows }, (_, i) => i + 1),
      show: false,
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: false,
      inRange: { color: ["#e8f5e9", "#e74c3c"] },
      show: false,
    },
    series: [
      {
        type: "heatmap",
        data,
        label: { show: false },
        emphasis: { itemStyle: { shadowBlur: 10 } },
      },
    ],
  };
};

const buildTimeseriesOption = (report, field, period) => {
  const ts = report?.timeseries?.[field]?.[period];
  if (!ts || !ts.dates?.length) return null;

  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 20, bottom: 50 },
    xAxis: { type: "category", data: ts.dates, axisLabel: { rotate: 45 } },
    yAxis: { type: "value" },
    series: [
      {
        type: "line",
        data: ts.values,
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { color: LINE_COLOR, width: 2 },
        itemStyle: { color: LINE_COLOR },
        areaStyle: { color: "rgba(29, 161, 167, 0.15)" },
      },
    ],
  };
};

const buildOutliersOption = (report, field) => {
  const o = report?.outliers?.[field];
  if (!o) return null;

  const categories = [t("outlierIQR"), t("outlierZScore")];
  const values = [o.iqr.count, o.zscore.count];

  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 30, bottom: 40 },
    xAxis: { type: "category", data: categories },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: values,
        itemStyle: { color: BAR_COLOR },
        barMaxWidth: 48,
        label: { show: true, position: "top", fontWeight: "bold" },
      },
    ],
  };
};

const buildComparisonHistogramOption = (report, fields) => {
  if (!fields.length) return null;
  const colors = [BAR_COLOR, LINE_COLOR, "#9b59b6", "#2ecc71", "#f39c12", "#e74c3c", "#3498db", "#1abc9c"];
  const series = [];
  for (let i = 0; i < fields.length; i++) {
    const h = report?.histograms?.[fields[i]];
    if (!h || !h.bins?.length) continue;
    const labels = h.bins.slice(0, -1).map((v, idx) => {
      const end = h.bins[idx + 1];
      return `${Number(v).toFixed(2)}-${Number(end).toFixed(2)}`;
    });
    series.push({
      name: fields[i],
      type: "bar",
      data: h.counts,
      barMaxWidth: Math.max(8, 24 - fields.length * 2),
      itemStyle: { color: colors[i % colors.length], opacity: 0.75 },
    });
  }
  if (!series.length) return null;
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 20, right: 20, top: 30, bottom: 40, containLabel: true },
    xAxis: { type: "category", data: series[0] ? Object.keys(series[0].data).map(() => "") : [], axisLabel: { rotate: 25 } },
    yAxis: { type: "value" },
    series,
  };
};

const buildChartOption = (report, category, type, feature) => {
  if (!report || !category) {
    return null;
  }

  if (category === "missing_rate") {
    return buildMissingRateOption(report, type);
  }

  if (category === "feature_distribution") {
    if (comparisonMode.value && selectedComparisonFields.value.length > 1) {
      return buildComparisonHistogramOption(report, selectedComparisonFields.value);
    }
    let histData = report;
    if (rebinData.value && rebinData.value.field === feature) {
      histData = {
        histograms: {
          [feature]: {
            bins: rebinData.value.bins,
            counts: rebinData.value.counts,
          },
        },
      };
    }
    return buildHistogramOption(histData, feature);
  }

  if (category === "violin") {
    return buildViolinOption(report, feature);
  }

  if (category === "scatter_matrix") {
    return buildScatterOption(report, scatterXField.value, scatterYField.value);
  }

  if (category === "missing_heatmap") {
    return buildMissingHeatmapOption(report);
  }

  if (category === "timeseries") {
    return buildTimeseriesOption(report, feature, timeseriesPeriod.value);
  }

  if (category === "outliers") {
    return buildOutliersOption(report, feature);
  }

  if (category === "correlation") {
    return buildCorrelationOption(report);
  }

  if (category === "boxplot") {
    return buildBoxplotOption(report);
  }

  if (category === "group_stats") {
    return buildGroupStatsOption(report, feature, groupAggregation.value);
  }

  if (category === "binning") {
    return buildBinningOption(report, feature, binningMethod.value);
  }

  if (category === "frequency") {
    return buildFrequencyOption(report, feature, type);
  }

  if (category === "pareto") {
    return buildParetoOption(report, feature);
  }

  if (category === "dtype_distribution") {
    return buildTypeDistributionOption(report, type);
  }

  if (category === "numeric_mean") {
    return buildNumericOption(report, "mean", type);
  }

  if (category === "numeric_max") {
    return buildNumericOption(report, "max", type);
  }

  if (category === "numeric_min") {
    return buildNumericOption(report, "min", type);
  }

  return null;
};

const renderChart = () => {
  if (!chartEl.value) {
    return;
  }

  if (!hasCharts.value || !chartOption.value) {
    if (chartInstance.value) {
      chartInstance.value.clear();
    }
    return;
  }

  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartEl.value);
  }

  chartInstance.value.setOption(chartOption.value, true);
};

const resizeChart = () => {
  if (chartInstance.value) {
    chartInstance.value.resize();
  }
};

const toggleChartOptions = () => {
  if (!hasCharts.value) {
    return;
  }

  showChartOptions.value = !showChartOptions.value;
};

const syncChartSelection = () => {
  if (!analysisOptions.value.length) {
    chartCategory.value = null;
    chartType.value = "bar";
    chartFeature.value = null;
    return;
  }

  if (!analysisOptions.value.some((option) => option.key === chartCategory.value)) {
    chartCategory.value = analysisOptions.value[0].key;
  }

  if (chartCategory.value === "feature_distribution") {
    chartType.value = "histogram";
    if (!histogramFeatures.value.includes(chartFeature.value)) {
      chartFeature.value = histogramFeatures.value[0] || null;
    }
  } else if (chartCategory.value === "frequency") {
    chartType.value = "bar";
    if (!frequencyFields.value.includes(chartFeature.value)) {
      chartFeature.value = frequencyFields.value[0] || null;
    }
  } else if (chartCategory.value === "violin") {
    chartType.value = "bar";
    if (!violinFields.value.includes(chartFeature.value)) {
      chartFeature.value = violinFields.value[0] || null;
    }
  } else if (chartCategory.value === "scatter_matrix") {
    chartType.value = "bar";
    const sf = scatterFields.value;
    if (!sf.includes(scatterXField.value)) scatterXField.value = sf[0] || "";
    if (!sf.includes(scatterYField.value) || scatterYField.value === scatterXField.value) {
      scatterYField.value = sf[1] || sf[0] || "";
    }
    chartFeature.value = null;
  } else if (chartCategory.value === "missing_heatmap") {
    chartType.value = "bar";
    chartFeature.value = null;
  } else if (chartCategory.value === "timeseries") {
    chartType.value = "bar";
    if (!timeseriesFields.value.includes(chartFeature.value)) {
      chartFeature.value = timeseriesFields.value[0] || null;
    }
  } else if (chartCategory.value === "outliers") {
    chartType.value = "bar";
    if (!outlierFields.value.includes(chartFeature.value)) {
      chartFeature.value = outlierFields.value[0] || null;
    }
  } else if (chartCategory.value === "boxplot") {
    chartType.value = "bar";
    chartFeature.value = null;
  } else if (chartCategory.value === "correlation") {
    chartType.value = "bar";
    chartFeature.value = null;
  } else if (chartCategory.value === "group_stats") {
    chartType.value = "bar";
    if (!groupCategoricalFields.value.includes(chartFeature.value)) {
      chartFeature.value = groupCategoricalFields.value[0] || null;
    }
  } else if (chartCategory.value === "binning") {
    chartType.value = "bar";
    if (!binningFields.value.includes(chartFeature.value)) {
      chartFeature.value = binningFields.value[0] || null;
    }
  } else if (chartCategory.value === "pareto") {
    chartType.value = "bar";
    if (!paretoFields.value.includes(chartFeature.value)) {
      chartFeature.value = paretoFields.value[0] || null;
    }
  } else {
    if (!["bar", "line"].includes(chartType.value)) {
      chartType.value = "bar";
    }
    chartFeature.value = null;
  }
};

const selectAnalysis = (key) => {
  chartCategory.value = key;
  syncChartSelection();
};

const selectChartType = (type) => {
  chartType.value = type;
};

const selectFeature = (feature) => {
  chartFeature.value = feature;
};

const rebin = async () => {
  if (!savedName.value || !chartFeature.value || chartCategory.value !== "feature_distribution") {
    return;
  }
  try {
    rebinData.value = await rebinApi(
      savedName.value,
      chartFeature.value,
      histogramBinCount.value,
      histogramNormalize.value
    );
  } catch {
    rebinData.value = null;
  }
};

const downloadChart = (format) => {
  if (!chartInstance.value) return;
  const url = chartInstance.value.getDataURL({
    type: format === "svg" ? "svg" : "png",
    pixelRatio: 2,
    backgroundColor: "#fff",
  });
  const link = document.createElement("a");
  link.download = `dataflowbi_chart.${format}`;
  link.href = url;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const applyFilter = async () => {
  if (!savedName.value) return;
  const includeFields = Object.keys(preview.value?.filter_info || {});
  try {
    const result = await filterApi(
      savedName.value,
      includeFields.length ? includeFields : null,
      Object.keys(filterNumericRanges.value).length ? filterNumericRanges.value : null,
      Object.keys(filterCategoricalValues.value).length ? filterCategoricalValues.value : null,
    );
    filteredData.value = result;
  } catch {
    filteredData.value = null;
  }
};

const resetFilter = () => {
  filterNumericRanges.value = {};
  filterCategoricalValues.value = {};
  filteredData.value = null;
  showFilterPanel.value = false;
};

const initFilterInfo = () => {
  const info = preview.value?.filter_info;
  if (!info) return;
  filterNumericRanges.value = {};
  filterCategoricalValues.value = {};
  for (const [field, meta] of Object.entries(info)) {
    if (meta.dtype?.startsWith("int") || meta.dtype?.startsWith("float")) {
      if (meta.min != null && meta.max != null) {
        filterNumericRanges.value[field] = [meta.min, meta.max];
      }
    }
  }
};

const toggleComparisonField = (field) => {
  const idx = selectedComparisonFields.value.indexOf(field);
  if (idx >= 0) {
    selectedComparisonFields.value.splice(idx, 1);
  } else {
    selectedComparisonFields.value.push(field);
  }
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
  syncChartSelection();
  showChartOptions.value = false;
  await runUpload();
};

watch(reportData, () => {
  syncChartSelection();
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

watch([chartCategory, chartType, chartFeature], () => {
  nextTick(renderChart);
});

watch([histogramBinCount, histogramNormalize], () => {
  if (chartCategory.value === "feature_distribution") {
    rebin();
  }
});

watch(rebinData, () => {
  nextTick(renderChart);
});

watch(analysisOptions, () => {
  syncChartSelection();
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
    showChartOptions.value = false;
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
  chartCategory.value = null;
  chartFeature.value = null;
  showChartOptions.value = false;
  savedName.value = "";
  rebinData.value = null;
  histogramBinCount.value = 10;
  histogramNormalize.value = false;
  groupAggregation.value = "mean";
  binningMethod.value = "equal_width";
  scatterXField.value = "";
  scatterYField.value = "";
  timeseriesPeriod.value = "daily";
  comparisonMode.value = false;
  selectedComparisonFields.value = [];
  showFilterPanel.value = false;
  filterNumericRanges.value = {};
  filterCategoricalValues.value = {};
  filteredData.value = null;
};

const runUpload = async () => {
  if (!selectedFile.value) {
    return;
  }

  isUploading.value = true;
  errorMessage.value = "";

  try {
    preview.value = await uploadDataset(selectedFile.value);
    savedName.value = preview.value?.saved_name || "";
    showAllFields.value = false;
    hasParsed.value = true;
    rebinData.value = null;
    histogramBinCount.value = 10;
    histogramNormalize.value = false;
    initFilterInfo();
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || t("uploadError");
  } finally {
    isUploading.value = false;
  }
};
</script>
