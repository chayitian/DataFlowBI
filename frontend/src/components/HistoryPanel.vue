<template>
  <div v-if="show" class="selection-overlay" @click.self="$emit('close')">
    <div
      :class="[
        'selection-panel',
        selectionMode === 'drawer' ? 'is-drawer' : 'is-dialog',
      ]"
    >
      <div class="selection-header">
        <h3>{{ t("historyTitle") }}</h3>
        <button class="icon-button" type="button" @click="$emit('close')">×</button>
      </div>
      <div class="selection-body">
        <div v-if="loading" class="loading">{{ t("loading") }}</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else-if="records.length === 0" class="empty">{{ t("historyEmpty") }}</div>
        <table v-else class="history-table">
          <thead>
            <tr>
              <th>{{ t("filename") }}</th>
              <th>{{ t("rows") }}</th>
              <th>{{ t("columns") }}</th>
              <th>{{ t("versionLabel") }}</th>
              <th>{{ t("tagLabel") }}</th>
              <th>{{ t("uploadTime") }}</th>
              <th>{{ t("action") }}</th>
              <th>{{ t("compareLabel") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in records" :key="record.id">
              <td>{{ record.original_filename }}</td>
              <td>{{ record.row_count }}</td>
              <td>{{ record.column_count }}</td>
              <td>{{ record.version ?? "-" }}</td>
              <td>{{ record.tag || "-" }}</td>
              <td>{{ formatTime(record.created_at) }}</td>
              <td>
                <button class="load-btn" :disabled="loadingId === record.id" @click="loadRecord(record)">
                  {{ loadingId === record.id ? t("loading") : t("loadRecord") }}
                </button>
              </td>
              <td>
                <button
                  v-if="!compareBase"
                  class="compare-btn"
                  @click="setCompareBase(record)"
                >
                  {{ t("compareSetBase") }}
                </button>
                <button
                  v-else
                  class="compare-btn"
                  :disabled="compareBase.id === record.id"
                  @click="runCompare(record)"
                >
                  {{ t("compareWith") }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="compareBase" class="compare-base">
          <span>{{ t("compareBase") }}: #{{ compareBase.id }} (v{{ compareBase.version ?? "-" }})</span>
          <button class="ghost-button" type="button" @click="clearCompare">{{ t("compareClear") }}</button>
        </div>
        <div v-if="compareError" class="error">{{ compareError }}</div>
        <div v-if="compareResult" class="compare-panel">
          <div class="compare-title">{{ t("compareResult") }}</div>
          <div class="compare-grid">
            <div></div>
            <div>{{ t("compareBase") }}</div>
            <div>{{ t("compareTarget") }}</div>
            <div>{{ t("compareDelta") }}</div>
            <div>{{ t("rows") }}</div>
            <div>{{ compareResult.from.rows }}</div>
            <div>{{ compareResult.to.rows }}</div>
            <div>{{ compareResult.delta.rows }}</div>
            <div>{{ t("cleanMissingRateAvg") }}</div>
            <div>{{ formatPercent(compareResult.from.missing_rate_avg) }}</div>
            <div>{{ formatPercent(compareResult.to.missing_rate_avg) }}</div>
            <div>{{ formatPercent(compareResult.delta.missing_rate_avg) }}</div>
            <div>{{ t("cleanQualityOverall") }}</div>
            <div>{{ formatScore(compareResult.from.quality_overall) }}</div>
            <div>{{ formatScore(compareResult.to.quality_overall) }}</div>
            <div>{{ formatScore(compareResult.delta.quality_overall) }}</div>
          </div>
        </div>
        <div v-if="totalPages > 1" class="pagination">
          <button :disabled="page <= 1" @click="changePage(page - 1)">&laquo;</button>
          <span>{{ page }} / {{ totalPages }}</span>
          <button :disabled="page >= totalPages" @click="changePage(page + 1)">&raquo;</button>
        </div>
      </div>
      <div class="selection-footer">
        <button class="ghost-button" type="button" @click="$emit('close')">
          {{ t("cancel") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useI18n } from "../composables/useI18n";
import { getHistory, compareHistory } from "../api/upload";

const { t } = useI18n();

const props = defineProps({
  show: Boolean,
  selectionMode: String,
});

const emit = defineEmits(["close", "select"]);

const records = ref([]);
const loading = ref(false);
const loadingId = ref(null);
const error = ref("");
const compareError = ref("");
const page = ref(1);
const total = ref(0);
const pageSize = 10;
const compareBase = ref(null);
const compareResult = ref(null);

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)));

const fetchHistory = async () => {
  loading.value = true;
  error.value = "";
  try {
    const data = await getHistory(pageSize, (page.value - 1) * pageSize);
    records.value = data.records || [];
    total.value = data.total || 0;
  } catch (e) {
    error.value = e?.response?.data?.detail || "Failed to load history";
    records.value = [];
  } finally {
    loading.value = false;
  }
};

const loadRecord = async (record) => {
  loadingId.value = record.id;
  try {
    emit("select", record);
  } finally {
    loadingId.value = null;
  }
};

const setCompareBase = (record) => {
  compareBase.value = record;
  compareResult.value = null;
  compareError.value = "";
};

const clearCompare = () => {
  compareBase.value = null;
  compareResult.value = null;
  compareError.value = "";
};

const runCompare = async (record) => {
  if (!compareBase.value || compareBase.value.id === record.id) return;
  compareError.value = "";
  try {
    compareResult.value = await compareHistory(compareBase.value.id, record.id);
  } catch (e) {
    compareError.value = e?.response?.data?.detail || "Compare failed";
    compareResult.value = null;
  }
};

const changePage = (newPage) => {
  page.value = newPage;
  fetchHistory();
};

const formatTime = (timeStr) => {
  if (!timeStr) return "";
  const d = new Date(timeStr);
  return d.toLocaleString();
};

const formatPercent = (value) => {
  if (value === null || value === undefined) return "-";
  return `${(Number(value) * 100).toFixed(1)}%`;
};

const formatScore = (value) => {
  if (value === null || value === undefined) return "-";
  return Number(value).toFixed(1);
};

watch(page, () => { fetchHistory(); });

watch(() => props.show, (val) => {
  if (val) {
    page.value = 1;
    fetchHistory();
    clearCompare();
  }
});
</script>

<style scoped>
.loading, .empty, .error {
  text-align: center;
  padding: 40px 0;
  color: #888;
}
.error { color: #e74c3c; }
.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.history-table th, .history-table td {
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid #eee;
}
.history-table th {
  font-weight: 600;
  color: #555;
  background: #fafafa;
}
.history-table tbody tr:hover {
  background: #f5f7fa;
}
.load-btn {
  padding: 4px 12px;
  border: 1px solid #3b82f6;
  background: #3b82f6;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.load-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.compare-btn {
  padding: 4px 10px;
  border: 1px solid #10b981;
  background: #10b981;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}
.compare-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.compare-base {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding: 8px 12px;
  background: #f3f4f6;
  border-radius: 8px;
  font-size: 12px;
  color: #374151;
}
.compare-panel {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fafafa;
}
.compare-title {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 13px;
}
.compare-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 6px 10px;
  font-size: 12px;
  color: #4b5563;
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
}
.pagination button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
}
.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
