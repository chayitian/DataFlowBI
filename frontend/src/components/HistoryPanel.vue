<template>
  <div v-if="show" class="dialog-overlay" @click.self="$emit('close')">
    <div class="history-dialog">
      <div class="dialog-header">
        <h2>{{ t("historyTitle") }}</h2>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>
      <div class="dialog-body">
        <div v-if="loading" class="loading">{{ t("loading") }}</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else-if="records.length === 0" class="empty">{{ t("historyEmpty") }}</div>
        <table v-else class="history-table">
          <thead>
            <tr>
              <th>{{ t("filename") }}</th>
              <th>{{ t("rows") }}</th>
              <th>{{ t("columns") }}</th>
              <th>{{ t("uploadTime") }}</th>
              <th>{{ t("action") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in records" :key="record.id">
              <td>{{ record.original_filename }}</td>
              <td>{{ record.row_count }}</td>
              <td>{{ record.column_count }}</td>
              <td>{{ formatTime(record.created_at) }}</td>
              <td>
                <button class="load-btn" :disabled="loadingId === record.id" @click="loadRecord(record)">
                  {{ loadingId === record.id ? t("loading") : t("loadRecord") }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="totalPages > 1" class="pagination">
          <button :disabled="page <= 1" @click="changePage(page - 1)">&laquo;</button>
          <span>{{ page }} / {{ totalPages }}</span>
          <button :disabled="page >= totalPages" @click="changePage(page + 1)">&raquo;</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useI18n } from "../composables/useI18n";
import { getHistory } from "../api/upload";

const { t } = useI18n();

const props = defineProps({
  show: Boolean,
});

const emit = defineEmits(["close", "select"]);

const records = ref([]);
const loading = ref(false);
const loadingId = ref(null);
const error = ref("");
const page = ref(1);
const total = ref(0);
const pageSize = 10;

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

const changePage = (newPage) => {
  page.value = newPage;
  fetchHistory();
};

const formatTime = (timeStr) => {
  if (!timeStr) return "";
  const d = new Date(timeStr);
  return d.toLocaleString();
};

watch(page, () => { fetchHistory(); });

watch(() => props.show, (val) => {
  if (val) {
    page.value = 1;
    fetchHistory();
  }
});
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.history-dialog {
  background: #fff;
  border-radius: 12px;
  width: 720px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
}
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 0;
}
.dialog-header h2 {
  margin: 0;
  font-size: 18px;
}
.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}
.dialog-body {
  padding: 16px 24px 24px;
  overflow-y: auto;
  flex: 1;
}
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
