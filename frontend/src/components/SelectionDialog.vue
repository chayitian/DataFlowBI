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
        <h3>{{ t("selectionTitle") }}</h3>
        <button class="icon-button" type="button" @click="$emit('close')">
          ×
        </button>
      </div>
      <div class="selection-body">
        <div class="selection-group">
          <div class="selection-label">{{ t("selectionBasics") }}</div>
          <label class="checkbox">
            <input type="checkbox" :checked="selection.preview" @change="$emit('update:selection', { ...selection, preview: $event.target.checked })" />
            <span>{{ t("selectionPreview") }}</span>
          </label>
          <label class="checkbox">
            <input type="checkbox" :checked="selection.report" @change="$emit('update:selection', { ...selection, report: $event.target.checked })" />
            <span>{{ t("selectionReport") }}</span>
          </label>
          <label class="checkbox" :class="{ disabled: !selection.report }">
            <input
              type="checkbox"
              :checked="selection.sample"
              :disabled="!selection.report"
              @change="$emit('update:selection', { ...selection, sample: $event.target.checked })"
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
              :checked="selection.charts_enabled"
              @change="$emit('update:selection', { ...selection, charts_enabled: $event.target.checked })"
            />
            <span>{{ t("selectionChartsEnabled") }}</span>
          </label>
        </div>
      </div>
      <div class="selection-footer">
        <button class="ghost-button" type="button" @click="$emit('close')">
          {{ t("cancel") }}
        </button>
        <button
          class="primary-btn"
          type="button"
          :disabled="disabled"
          @click="$emit('confirm')"
        >
          {{ t("confirm") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from "../composables/useI18n";

defineProps({
  show: Boolean,
  selection: Object,
  selectionMode: String,
  disabled: Boolean,
});

defineEmits(["close", "confirm", "update:selection"]);

const { t } = useI18n();
</script>
