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
