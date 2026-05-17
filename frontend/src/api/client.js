import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const detail = error.response.data?.detail || error.message;
      console.error(`[API Error ${error.response.status}] ${detail}`);
    } else if (error.request) {
      console.error("[API Error] No response received:", error.message);
    } else {
      console.error("[API Error]", error.message);
    }
    return Promise.reject(error);
  }
);
