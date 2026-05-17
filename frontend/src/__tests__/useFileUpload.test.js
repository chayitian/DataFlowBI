import { describe, it, expect, beforeEach, vi } from "vitest";

vi.mock("../api/upload", () => ({
  uploadDataset: vi.fn(),
  filterData: vi.fn(),
}));

import { uploadDataset, filterData as filterApi } from "../api/upload";
import { useFileUpload } from "../composables/useFileUpload";

const mockPreview = {
  saved_name: "abc123",
  fields: ["name", "age", "salary"],
  filter_info: {
    name: { dtype: "object", values: ["Alice", "Bob"] },
    age: { dtype: "int64", min: 25, max: 35, mean: 30 },
    salary: { dtype: "float64", min: 50000, max: 70000, mean: 60000 },
  },
  report: { dtypes: { name: "object" }, numeric_summary: {} },
};

const mockFilterResult = {
  fields: ["name", "age"],
  rows: 5,
  columns: 2,
  report: { dtypes: { name: "object" } },
};

describe("useFileUpload", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const {
      onFileChange, preview, errorMessage, filteredData,
      filterNumericRanges, filterCategoricalValues, selectedFields,
      showFilterPanel, hasParsed, savedName,
    } = useFileUpload();
    onFileChange({ target: { files: [] } });
  });

  it("has initial default state", () => {
    const { selectedFile, preview, isUploading, errorMessage, hasParsed, showFilterPanel } = useFileUpload();
    expect(selectedFile.value).toBeNull();
    expect(preview.value).toBeNull();
    expect(isUploading.value).toBe(false);
    expect(errorMessage.value).toBe("");
    expect(hasParsed.value).toBe(false);
    expect(showFilterPanel.value).toBe(false);
  });

  it("onFileChange resets state", () => {
    const file = new File(["data"], "test.csv", { type: "text/csv" });
    const { onFileChange, selectedFile, preview, errorMessage, hasParsed } = useFileUpload();
    onFileChange({ target: { files: [file] } });
    expect(selectedFile.value).toBe(file);
    expect(preview.value).toBeNull();
    expect(errorMessage.value).toBe("");
    expect(hasParsed.value).toBe(false);
  });

  it("runUpload sets preview on success", async () => {
    uploadDataset.mockResolvedValue(mockPreview);
    const { runUpload, selectedFile, preview, savedName, hasParsed } = useFileUpload();
    selectedFile.value = new File(["data"], "test.csv", { type: "text/csv" });
    await runUpload();
    expect(preview.value).toEqual(mockPreview);
    expect(savedName.value).toBe("abc123");
    expect(hasParsed.value).toBe(true);
  });

  it("runUpload sets errorMessage on failure", async () => {
    uploadDataset.mockRejectedValue({ response: { data: { detail: "Upload failed" } } });
    const { runUpload, selectedFile, preview, errorMessage } = useFileUpload();
    selectedFile.value = new File(["data"], "test.csv", { type: "text/csv" });
    await runUpload();
    expect(preview.value).toBeNull();
    expect(errorMessage.value).toBe("Upload failed");
  });

  it("runUpload skips without file", async () => {
    const { runUpload, selectedFile } = useFileUpload();
    selectedFile.value = null;
    await runUpload();
    expect(uploadDataset).not.toHaveBeenCalled();
  });

  it("initFilterInfo sets selectedFields to all fields", () => {
    const { initFilterInfo, preview, selectedFields } = useFileUpload();
    preview.value = mockPreview;
    initFilterInfo();
    expect(selectedFields.value).toEqual(["name", "age", "salary"]);
  });

  it("applyFilter calls API and sets filteredData", async () => {
    filterApi.mockResolvedValue(mockFilterResult);
    const { applyFilter, savedName, filteredData, selectedFields } = useFileUpload();
    savedName.value = "test123";
    selectedFields.value = ["name", "age"];
    await applyFilter();
    expect(filterApi).toHaveBeenCalledWith("test123", ["name", "age"], null, null);
    expect(filteredData.value).toEqual(mockFilterResult);
  });

  it("applyFilter with null selectedFields sends null", async () => {
    filterApi.mockResolvedValue(mockFilterResult);
    const { applyFilter, savedName, selectedFields } = useFileUpload();
    savedName.value = "test123";
    selectedFields.value = null;
    await applyFilter();
    expect(filterApi).toHaveBeenCalledWith("test123", null, null, null);
  });

  it("applyFilter handles API error gracefully", async () => {
    filterApi.mockRejectedValue(new Error("Network error"));
    const { applyFilter, savedName, filteredData } = useFileUpload();
    savedName.value = "test123";
    await applyFilter();
    expect(filteredData.value).toBeNull();
  });

  it("applyFilter skips without savedName", async () => {
    const { applyFilter, savedName } = useFileUpload();
    savedName.value = "";
    await applyFilter();
    expect(filterApi).not.toHaveBeenCalled();
  });

  it("resetFilter restores default state", () => {
    const { resetFilter, selectedFields, filterNumericRanges, filterCategoricalValues, filteredData, showFilterPanel, preview } = useFileUpload();
    preview.value = mockPreview;
    selectedFields.value = ["name"];
    filterNumericRanges.value = { age: [20, 30] };
    filterCategoricalValues.value = { dept: ["Eng"] };
    filteredData.value = mockFilterResult;
    showFilterPanel.value = true;
    resetFilter();
    expect(selectedFields.value).toEqual(["name", "age", "salary"]);
    expect(filterNumericRanges.value).toEqual({});
    expect(filterCategoricalValues.value).toEqual({});
    expect(filteredData.value).toBeNull();
    expect(showFilterPanel.value).toBe(false);
  });

  it("toggleFields toggles showAllFields", () => {
    const { toggleFields, showAllFields } = useFileUpload();
    expect(showAllFields.value).toBe(false);
    toggleFields();
    expect(showAllFields.value).toBe(true);
    toggleFields();
    expect(showAllFields.value).toBe(false);
  });

  it("activeReport uses filteredData when available", () => {
    const { activeReport, preview, filteredData } = useFileUpload();
    preview.value = mockPreview;
    filteredData.value = { report: { dtypes: { filtered: true } } };
    expect(activeReport.value).toEqual({ dtypes: { filtered: true } });
  });

  it("activeReport falls back to reportData", () => {
    const { activeReport, preview, filteredData } = useFileUpload();
    preview.value = mockPreview;
    filteredData.value = null;
    expect(activeReport.value).toEqual(mockPreview.report);
  });

  it("reportStatsRows builds rows from report data", () => {
    const { reportStatsRows, preview } = useFileUpload();
    preview.value = mockPreview;
    const rows = reportStatsRows.value;
    expect(rows).toHaveLength(1);
    expect(rows[0].field).toBe("name");
    expect(rows[0].dtype).toBe("object");
  });
});
