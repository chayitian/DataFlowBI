import { apiClient } from "./client";

export async function trainModel(payload) {
  // payload 包含 saved_name 以及 MachineLearningDialog 生成的模型配置。
  const response = await apiClient.post("/ml/train", payload);
  return response.data;
}
