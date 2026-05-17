<template>
  <div class="top-actions">
    <div class="lang-menu">
      <button class="lang-button" type="button" @click="$emit('toggle')">
        {{ t("settings") }}
      </button>
      <div v-if="show" class="lang-dropdown">
        <div class="lang-title">{{ t("language") }}</div>
        <button
          :class="['lang-option', { active: locale === 'zh' }]"
          type="button"
          @click="$emit('update:locale', 'zh')"
        >
          {{ t("langChinese") }}
        </button>
        <button
          :class="['lang-option', { active: locale === 'en' }]"
          type="button"
          @click="$emit('update:locale', 'en')"
        >
          {{ t("langEnglish") }}
        </button>
        <div class="settings-divider"></div>
        <div class="lang-title">{{ t("selectionModeTitle") }}</div>
        <button
          :class="['lang-option', { active: selectionMode === 'dialog' }]"
          type="button"
          @click="$emit('update:selectionMode', 'dialog')"
        >
          {{ t("selectionModeDialog") }}
        </button>
        <button
          :class="['lang-option', { active: selectionMode === 'drawer' }]"
          type="button"
          @click="$emit('update:selectionMode', 'drawer')"
        >
          {{ t("selectionModeDrawer") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from "../composables/useI18n";

const props = defineProps({
  show: Boolean,
  locale: String,
  selectionMode: String,
});

defineEmits(["toggle", "update:locale", "update:selectionMode"]);

const { t } = useI18n();
</script>
