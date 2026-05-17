import { ref, computed } from "vue";
import { uploadDataset, filterData as filterApi } from "../api/upload";

const MAX_FILE_SIZE = 100 * 1024 * 1024;
const selectedFile = ref(null);
const preview = ref(null);
const isUploading = ref(false);
const errorMessage = ref("");
const showAllFields = ref(false);
const savedName = ref("");
const filteredData = ref(null);
const filterNumericRanges = ref({});
const filterCategoricalValues = ref({});
const showFilterPanel = ref(false);
const hasParsed = ref(false);
const selectedFields = ref(null);
const fieldLimit = 5;

export function useFileUpload() {
  const reportData = computed(() => preview.value?.report || null);
  const numericSummary = computed(() => reportData.value?.numeric_summary || {});
  const sampleRows = computed(() => reportData.value?.sample_rows || []);
  const totalFields = computed(() => preview.value?.fields?.length ?? 0);
  const visibleFields = computed(() => {
    const fields = preview.value?.fields || [];
    return showAllFields.value ? fields : fields.slice(0, fieldLimit);
  });
  const hasMoreFields = computed(() => totalFields.value > fieldLimit);
  const sampleColumns = computed(() => {
    if (!sampleRows.value.length) return [];
    return Object.keys(sampleRows.value[0]);
  });
  const activeReport = computed(() => filteredData.value?.report || reportData.value);

  const reportStatsRows = computed(() => {
    if (!reportData.value) return [];
    const dtypes = reportData.value.dtypes || {};
    const missing = reportData.value.missing || {};
    const missingRate = reportData.value.missing_rate || {};
    const summary = reportData.value.numeric_summary || {};
    return Object.keys(dtypes).map((field) => ({
      field,
      dtype: dtypes[field],
      missing: missing[field] ?? 0,
      missingRate: missingRate[field] ?? 0,
      count: summary[field]?.count ?? null,
      mean: summary[field]?.mean ?? null,
      std: summary[field]?.std ?? null,
      min: summary[field]?.min ?? null,
      max: summary[field]?.max ?? null,
    }));
  });

  const toggleFields = () => { showAllFields.value = !showAllFields.value; };

  const onFileChange = (event) => {
    const [file] = event.target.files || [];
    selectedFile.value = file || null;
    preview.value = null;
    errorMessage.value = "";
    showAllFields.value = false;
    hasParsed.value = false;
    savedName.value = "";
    filteredData.value = null;
    filterNumericRanges.value = {};
    filterCategoricalValues.value = {};
    selectedFields.value = null;
    showFilterPanel.value = false;
  };

  const runUpload = async (onError) => {
    if (!selectedFile.value) return;
    if (selectedFile.value.size > MAX_FILE_SIZE) {
      const maxMb = MAX_FILE_SIZE / (1024 * 1024);
      errorMessage.value = `File too large. Maximum size is ${maxMb}MB.`;
      if (onError) onError(errorMessage.value);
      return;
    }
    isUploading.value = true;
    errorMessage.value = "";
    try {
      preview.value = await uploadDataset(selectedFile.value);
      savedName.value = preview.value?.saved_name || "";
      showAllFields.value = false;
      hasParsed.value = true;
      initFilterInfo();
    } catch (error) {
      const msg = error?.response?.data?.detail || "Upload failed";
      errorMessage.value = msg;
      if (onError) onError(msg);
    } finally {
      isUploading.value = false;
    }
  };

  const initFilterInfo = () => {
    const info = preview.value?.filter_info;
    if (!info) return;
    selectedFields.value = preview.value?.fields || null;
    filterNumericRanges.value = {};
    filterCategoricalValues.value = {};
  };

  const applyFilter = async () => {
    if (!savedName.value) return;
    const includeFields = selectedFields.value?.length ? selectedFields.value : null;
    try {
      const result = await filterApi(
        savedName.value,
        includeFields,
        Object.keys(filterNumericRanges.value).length ? filterNumericRanges.value : null,
        Object.keys(filterCategoricalValues.value).length ? filterCategoricalValues.value : null
      );
      filteredData.value = result;
    } catch {
      filteredData.value = null;
    }
  };

  const resetFilter = () => {
    filterNumericRanges.value = {};
    filterCategoricalValues.value = {};
    selectedFields.value = preview.value?.fields || null;
    filteredData.value = null;
    showFilterPanel.value = false;
  };

  return {
    selectedFile, preview, isUploading, errorMessage, showAllFields, savedName,
    filteredData, filterNumericRanges, filterCategoricalValues, showFilterPanel, hasParsed, selectedFields,
    reportData, numericSummary, sampleRows, totalFields, visibleFields, hasMoreFields,
    sampleColumns, reportStatsRows, activeReport,
    onFileChange, runUpload, initFilterInfo, applyFilter, resetFilter, toggleFields,
  };
}
