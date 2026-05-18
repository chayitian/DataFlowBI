<template>
  <div class="chart-toolbar">
    <button
      class="chart-options-toggle"
      type="button"
      :disabled="!hasCharts"
      @click="$emit('toggleOptions')"
    >
      <span>{{ showOptions ? t("collapseCharts") : t("expandCharts") }}</span>
      <span
        :class="[
          'chart-toggle-arrow',
          { open: showOptions },
        ]"
      >
        ▾
      </span>
    </button>
    <div class="chart-current">
      <span>{{ title }}</span>
    </div>
    <div v-if="hasCharts" class="chart-download-group">
      <button
        :class="['chart-download-btn', { active: showFilter }]"
        type="button"
        @click="$emit('toggleFilter')"
      >
        {{ t("filterTitle") }}
      </button>
      <button
        :class="['chart-download-btn', { active: comparisonMode }]"
        type="button"
        @click="$emit('toggleComparison')"
      >
        {{ t("comparisonMode") }}
      </button>
      <button
        class="chart-download-btn"
        type="button"
        title="PNG"
        @click="$emit('download', 'png')"
      >
        {{ t("downloadPNG") }}
      </button>
      <button
        class="chart-download-btn"
        type="button"
        title="SVG"
        @click="$emit('download', 'svg')"
      >
        {{ t("downloadSVG") }}
      </button>
      <button
        class="chart-download-btn"
        type="button"
        @click="$emit('exportDocx')"
      >
        {{ t("exportWord") }}
      </button>
      <button
        class="chart-download-btn"
        type="button"
        @click="$emit('exportPdf')"
      >
        {{ t("exportPdf") }}
      </button>
      <button
        class="chart-download-btn"
        type="button"
        @click="$emit('exportExcel')"
      >
        {{ t("exportExcel") }}
      </button>
      <button
        class="chart-download-btn"
        type="button"
        @click="$emit('exportPptx')"
      >
        {{ t("exportPpt") }}
      </button>
      <button
        class="chart-download-btn"
        type="button"
        @click="$emit('setup')"
      >
        {{ t("chartSetupTitle") }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from "../composables/useI18n";

defineProps({
  showOptions: Boolean,
  hasCharts: Boolean,
  title: String,
  showFilter: Boolean,
  comparisonMode: Boolean,
});

defineEmits([
  "toggleOptions",
  "toggleFilter",
  "toggleComparison",
  "download",
  "setup",
  "exportDocx",
  "exportPdf",
  "exportExcel",
  "exportPptx",
]);

const { t } = useI18n();
</script>
