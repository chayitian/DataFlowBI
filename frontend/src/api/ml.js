import { apiClient } from "./client";

export async function trainModel(payload) {
  const response = await apiClient.post("/ml/train", payload);
  return response.data;
}
