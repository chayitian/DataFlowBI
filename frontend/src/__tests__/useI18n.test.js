import { describe, it, expect, beforeEach } from "vitest";
import { useI18n } from "../composables/useI18n";

describe("useI18n", () => {
  beforeEach(() => {
    const { setLanguage } = useI18n();
    setLanguage("zh");
  });

  it("returns zh translation by default", () => {
    const { t } = useI18n();
    expect(t("settings")).toBe("设置");
    expect(t("language")).toBe("语言");
  });

  it("switches to en", () => {
    const { t, setLanguage } = useI18n();
    setLanguage("en");
    expect(t("settings")).toBe("Settings");
    expect(t("language")).toBe("Language");
  });

  it("returns key for missing translations", () => {
    const { t } = useI18n();
    expect(t("nonexistent_key")).toBe("nonexistent_key");
  });

  it("exposes locale ref", () => {
    const { locale, setLanguage } = useI18n();
    expect(locale.value).toBe("zh");
    setLanguage("en");
    expect(locale.value).toBe("en");
  });

  it("handles empty string key", () => {
    const { t } = useI18n();
    expect(t("")).toBe("");
  });
});
