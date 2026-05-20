import { ref } from "vue";
import { en } from "../locales/en";
import { zh } from "../locales/zh";

// 应用内轻量 i18n 存储。新增 UI 文案时同时补充 zh 和 en，组件里调用 t("messageKey")，
// 避免硬编码显示文本。
const locale = ref("zh");

const messages = { zh, en };

const t = (key) => messages[locale.value]?.[key] ?? key;

const setLanguage = (value) => {
  locale.value = value;
};

export function useI18n() {
  return { locale, t, setLanguage };
}
