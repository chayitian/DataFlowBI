<template>
  <section class="report-section">
    <div class="report-header">
      <h2>{{ t("reportTitle") }}</h2>
      <p>{{ t("reportSubtitle") }}</p>
    </div>
    <div v-if="reportData" class="report-grid">
      <div class="report-card report-card--tall">
        <div class="card-title">{{ t("reportStatsTitle") }}</div>
        <div class="report-body">
          <div v-if="statsRows.length" class="report-table-wrapper">
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
                <tr v-for="row in statsRows" :key="row.field">
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
      <div v-if="showSample" class="report-card report-card--full">
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
</template>

<script setup>
import { computed } from "vue";
import { useI18n } from "../composables/useI18n";

const props = defineProps({
  reportData: Object,
  showSample: Boolean,
  sampleRows: Array,
  sampleColumns: Array,
  statsRows: Array,
});

const { t } = useI18n();

const formatPercent = (value) => {
  if (value === null || value === undefined) return "-";
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) return "-";
  return `${(numericValue * 100).toFixed(1)}%`;
};

const formatNumber = (value) => {
  if (value === null || value === undefined) return "-";
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) return String(value);
  return Number.isInteger(numericValue) ? numericValue.toString() : numericValue.toFixed(3);
};

const formatValue = (value) => {
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
};
</script>
