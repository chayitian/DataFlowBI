import { apiClient } from "./client";

// 轻量 API 包装让组件不用关心 axios 细节和 URL 字符串。

export async function uploadDataset(file) {
  // multipart 上传会返回预览元数据、报告和筛选信息。
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}

export async function rebinHistogram(savedName, field, binCount, normalize) {
  // 直方图分箱变化需要原始数据，因此由后端重新计算。
  const response = await apiClient.post("/rebin", null, {
    params: {
      saved_name: savedName,
      field,
      bin_count: binCount,
      normalize,
    },
  });
  return response.data;
}

export async function filterData(savedName, includeFields, numericRanges, categoricalValues) {
  // 仅预览筛选：更新报告/图表数据，但不保存历史记录。
  const response = await apiClient.post("/filter", {
    saved_name: savedName,
    include_fields: includeFields,
    numeric_ranges: numericRanges,
    categorical_values: categoricalValues,
  });
  return response.data;
}

export async function getHistory(limit = 20, offset = 0) {
  const response = await apiClient.get("/history", { params: { limit, offset } });
  return response.data;
}

export async function getHistoryDetail(recordId) {
  const response = await apiClient.get(`/history/${recordId}`);
  return response.data;
}

export async function getHistoryVersions(recordId) {
  const response = await apiClient.get(`/history/${recordId}/versions`);
  return response.data;
}

export async function compareHistory(fromId, toId) {
  const response = await apiClient.get("/history/compare", {
    params: { from_id: fromId, to_id: toId },
  });
  return response.data;
}

export async function importHistory(recordId) {
  const response = await apiClient.post(`/history/${recordId}/import`);
  return response.data;
}

export async function reloadHistory(recordId) {
  // 根据 upload_records 中的缓存文件路径，重新填充后端 DATA_CACHE。
  const response = await apiClient.post(`/history/${recordId}/reload`);
  return response.data;
}

export async function exportReportDocx(savedName, filename = "report", charts = []) {
  const response = await apiClient.post(
    "/export/docx",
    { saved_name: savedName, filename, charts },
    { responseType: "blob" }
  );
  return response.data;
}

export async function exportReportExcel(savedName, filename = "report") {
  const response = await apiClient.get("/export/excel", {
    params: { saved_name: savedName, filename },
    responseType: "blob",
  });
  return response.data;
}

export async function cleanData(savedName, missingHandling, outlierHandling, typeConversions) {
  // 清洗会保存新的数据集版本，并返回刷新的预览/报告。
  const response = await apiClient.post("/clean", {
    saved_name: savedName,
    missing_handling: missingHandling,
    outlier_handling: outlierHandling,
    type_conversions: typeConversions,
  });
  return response.data;
}

export async function engineerFeatures(savedName, numericTransforms, categoricalFields, datetimeFields) {
  // 特征工程也会保存带有新增列的数据集版本。
  const response = await apiClient.post("/feature-engineering", {
    saved_name: savedName,
    numeric_transforms: numericTransforms,
    categorical_fields: categoricalFields,
    datetime_fields: datetimeFields,
  });
  return response.data;
}

export async function getCleanTemplates() {
  const response = await apiClient.get("/clean/templates");
  return response.data;
}

export async function exportReportPdf(savedName, filename = "report", charts = []) {
  const response = await apiClient.post(
    "/export/pdf",
    { saved_name: savedName, filename, charts },
    { responseType: "blob" }
  );
  return response.data;
}

export async function exportReportPptx(savedName, filename = "report", charts = []) {
  const response = await apiClient.post(
    "/export/pptx",
    { saved_name: savedName, filename, charts },
    { responseType: "blob" }
  );
  return response.data;
}
