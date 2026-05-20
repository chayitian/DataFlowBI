<template>
  <div v-if="preview" class="hero-card">
    <div class="card-title">{{ t("previewSummary") }}</div>
    <div class="preview-grid">
      <div class="preview-item">
        <span>{{ t("filename") }}</span>
        <strong class="preview-filename" :title="preview.filename">{{ preview.filename }}</strong>
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
    <div class="fields">
      <span
        v-for="field in visibleFields"
        :key="field"
        class="field-chip"
      >
        {{ field }}
      </span>
    </div>
    <div v-if="hasMoreFields" class="fields-controls">
      <button class="fields-toggle" type="button" @click="$emit('toggleFields')">
        {{ showAllFields ? t("collapseFields") : t("expandFields") }}
      </button>
      <span class="fields-count">
        {{ visibleFields.length }} / {{ totalFields }} {{ t("fieldsUnit") }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useI18n } from "../composables/useI18n";

const props = defineProps({
  preview: Object,
  showAllFields: Boolean,
  totalFields: Number,
  visibleFields: Array,
  hasMoreFields: Boolean,
});

defineEmits(["toggleFields"]);

const { t } = useI18n();
</script>
