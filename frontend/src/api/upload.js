import { apiClient } from "./client";

export async function uploadDataset(file) {
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

export async function reloadHistory(recordId) {
  const response = await apiClient.post(`/history/${recordId}/reload`);
  return response.data;
}

export async function exportReportDocx(savedName, filename = "report") {
  const response = await apiClient.get("/export/docx", {
    params: { saved_name: savedName, filename },
    responseType: "blob",
  });
  return response.data;
}

export async function exportReportExcel(savedName, filename = "report") {
  const response = await apiClient.get("/export/excel", {
    params: { saved_name: savedName, filename },
    responseType: "blob",
  });
  return response.data;
}
