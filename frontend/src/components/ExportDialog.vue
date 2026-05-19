<template>
  <div v-if="show" class="selection-overlay" @click.self="$emit('close')">
    <div
      :class="[
        'selection-panel',
        selectionMode === 'drawer' ? 'is-drawer' : 'is-dialog',
      ]"
    >
      <div class="selection-header">
        <h3>{{ t("exportMenu") }}</h3>
        <button class="icon-button" type="button" @click="$emit('close')">×</button>
      </div>
      <div class="selection-body">
        <div class="selection-group">
          <div class="selection-label">{{ t("downloadLabel") }}</div>
          <div class="export-actions">
            <button class="export-action" type="button" @click="emitAction('download', 'png')">
              {{ t("downloadPNG") }}
            </button>
            <button class="export-action" type="button" @click="emitAction('download', 'svg')">
              {{ t("downloadSVG") }}
            </button>
          </div>
        </div>
        <div class="selection-group">
          <div class="selection-label">{{ t("exportLabel") }}</div>
          <div class="export-actions">
            <button class="export-action" type="button" @click="emitAction('exportDocx')">
              {{ t("exportWord") }}
            </button>
            <button class="export-action" type="button" @click="emitAction('exportPdf')">
              {{ t("exportPdf") }}
            </button>
            <button class="export-action" type="button" @click="emitAction('exportExcel')">
              {{ t("exportExcel") }}
            </button>
            <button class="export-action" type="button" @click="emitAction('exportPptx')">
              {{ t("exportPpt") }}
            </button>
          </div>
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
import { useI18n } from "../composables/useI18n";

defineProps({
  show: Boolean,
  selectionMode: String,
});

const emit = defineEmits([
  "close",
  "download",
  "exportDocx",
  "exportPdf",
  "exportExcel",
  "exportPptx",
]);

const { t } = useI18n();

const emitAction = (eventName, payload) => {
  emit(eventName, payload);
  emit("close");
};
</script>
