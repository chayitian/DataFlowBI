<template>
  <div
    v-if="showFilterPanel"
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
        <h3>{{ t("filterTitle") }}</h3>
        <button class="icon-button" type="button" @click="$emit('close')">
          ×
        </button>
      </div>
      <div class="selection-body">
        <div class="selection-group">
          <label class="checkbox">
            <input
              type="checkbox"
              :checked="allSelected"
              :indeterminate="someSelected && !allSelected"
              @change="toggleAll"
            />
            <span>{{ t("selectAll") }}</span>
          </label>
        </div>
        <div class="selection-group">
          <div class="filter-fields">
            <label v-for="field in allFields" :key="field" class="checkbox">
              <input type="checkbox" :checked="!selectedFields || selectedFields.includes(field)" @change="toggleField(field)" />
              <span>{{ field }}</span>
            </label>
          </div>
        </div>
        <div v-if="filterInfo && Object.keys(visibleFilterInfo).length" class="selection-group">
          <div class="filter-ranges">
            <div v-for="(meta, field) in visibleFilterInfo" :key="field" class="filter-field">
              <div class="filter-field-label">{{ field }} <span class="filter-field-type">({{ meta.dtype }})</span></div>
              <div v-if="meta.min != null && meta.max != null" class="filter-range-row">
                <input
                  type="range"
                  class="histogram-slider filter-slider"
                  :min="meta.min"
                  :max="meta.max"
                  :value="(ranges[field] || [meta.min, meta.max])[0]"
                  @input="update(field, 0, Number($event.target.value))"
                />
                <input
                  type="range"
                  class="histogram-slider filter-slider"
                  :min="meta.min"
                  :max="meta.max"
                  :value="(ranges[field] || [meta.min, meta.max])[1]"
                  @input="update(field, 1, Number($event.target.value))"
                />
                <span class="filter-range-label">
                  {{ formatNumber((ranges[field] || [meta.min, meta.max])[0]) }} — {{ formatNumber((ranges[field] || [meta.min, meta.max])[1]) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="selection-footer">
        <button class="ghost-button" type="button" @click="$emit('reset')">
          {{ t("filterReset") }}
        </button>
        <button class="primary-btn" type="button" @click="$emit('apply')">
          {{ t("filterApply") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useI18n } from "../composables/useI18n";

const props = defineProps({
  showFilterPanel: Boolean,
  filterInfo: Object,
  ranges: Object,
  allFields: Array,
  selectedFields: Array,
  selectionMode: String,
});

const emit = defineEmits(["update:ranges", "apply", "reset", "update:selectedFields", "close"]);

const { t } = useI18n();

const allSelected = computed(() => !props.selectedFields);
const someSelected = computed(() => {
  if (!props.selectedFields) return false;
  return props.selectedFields.length > 0;
});

const visibleFilterInfo = computed(() => {
  const info = props.filterInfo;
  const selected = props.selectedFields;
  if (!info) return {};
  if (!selected) return info;
  return Object.fromEntries(
    Object.entries(info).filter(([field]) => selected.includes(field))
  );
});

const toggleAll = () => {
  if (allSelected.value) {
    emit("update:selectedFields", []);
  } else {
    emit("update:selectedFields", null);
  }
};

const toggleField = (field) => {
  const current = props.selectedFields || props.allFields;
  const idx = current.indexOf(field);
  const next = idx >= 0 ? current.filter((f) => f !== field) : [...current, field];
  emit("update:selectedFields", next.length ? next : null);
};

const formatNumber = (value) => {
  if (value === null || value === undefined) return "-";
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  return Number.isInteger(n) ? n.toString() : n.toFixed(3);
};

const update = (field, idx, value) => {
  const current = props.ranges[field] || [props.filterInfo[field].min, props.filterInfo[field].max];
  const next = [...current];
  next[idx] = value;
  emit("update:ranges", { ...props.ranges, [field]: next });
};
</script>
