import { describe, it, expect, beforeEach } from "vitest";
import { useSelection } from "../composables/useSelection";

describe("useSelection", () => {
  let selection;

  beforeEach(() => {
    selection = useSelection();
    selection.chartConfigApplied.value = false;
    selection.selection.value = selection.cloneSelection(selection.appliedSelection.value);
  });

  it("has default selection values", () => {
    const { appliedSelection } = useSelection();
    expect(appliedSelection.value.preview).toBe(true);
    expect(appliedSelection.value.report).toBe(true);
    expect(appliedSelection.value.sample).toBe(false);
    expect(appliedSelection.value.charts_enabled).toBe(true);
  });

  it("normalizeSelection ensures sample requires report", () => {
    const { normalizeSelection } = useSelection();
    const result = normalizeSelection({ preview: true, report: false, sample: true, charts_enabled: true });
    expect(result.sample).toBe(false);
  });

  it("normalizeSelection coerces booleans", () => {
    const { normalizeSelection } = useSelection();
    const result = normalizeSelection({ preview: 1, report: "yes", sample: null, charts_enabled: undefined });
    expect(result.preview).toBe(true);
    expect(result.report).toBe(true);
    expect(result.sample).toBe(false);
    expect(result.charts_enabled).toBe(false);
  });

  it("cloneSelection deep clones", () => {
    const { cloneSelection } = useSelection();
    const original = { a: 1, b: { c: 2 } };
    const cloned = cloneSelection(original);
    expect(cloned).toEqual(original);
    expect(cloned).not.toBe(original);
    expect(cloned.b).not.toBe(original.b);
  });

  it("openSelection copies appliedSelection to temp", () => {
    const { openSelection, selection, appliedSelection, showSelection } = useSelection();
    appliedSelection.value = { preview: false, report: false, sample: false, charts_enabled: false };
    openSelection();
    expect(selection.value).toEqual(appliedSelection.value);
    expect(showSelection.value).toBe(true);
  });

  it("closeSelection hides the panel", () => {
    const { closeSelection, showSelection } = useSelection();
    showSelection.value = true;
    closeSelection();
    expect(showSelection.value).toBe(false);
  });

  it("confirmSelection applies selection and hides panel", () => {
    const { selection, appliedSelection, confirmSelection, showSelection } = useSelection();
    selection.value = { preview: false, report: true, sample: true, charts_enabled: false };
    confirmSelection();
    expect(appliedSelection.value.preview).toBe(false);
    expect(appliedSelection.value.sample).toBe(true);
    expect(showSelection.value).toBe(false);
  });

  it("confirmChartSetup copies temp to applied and sets chartConfigApplied", () => {
    const { confirmChartSetup, tempChartTypes, appliedChartTypes, chartConfigApplied, showChartSetup } = useSelection();
    tempChartTypes.value = { missing_rate: false };
    confirmChartSetup();
    expect(appliedChartTypes.value.missing_rate).toBe(false);
    expect(chartConfigApplied.value).toBe(true);
    expect(showChartSetup.value).toBe(false);
  });

  it("showSampleSection requires showReportSection", () => {
    const hasParsedRef = { value: true };
    const sel = useSelection({ hasParsedRef });
    expect(sel.showReportSection.value).toBe(true);
    expect(sel.showSampleSection.value).toBe(true);

    sel.appliedSelection.value = { preview: false, report: false, sample: true, charts_enabled: false };
    expect(sel.showSampleSection.value).toBe(false);
  });
});
