import type {
  AnalyzeResponse,
  BatchAnalyzeResponse,
  BatchInspectResponse,
  BatchRowResult,
  HealthResponse,
  HistoryListResponse,
  ModelInsightsResponse,
  OCRResponse,
  SettingsModel,
} from "../types/messageshield";

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
      }
    } catch {
      // Ignore parse error on non-JSON responses
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export const api = {
  getHealth: () => requestJson<HealthResponse>("/api/health"),

  analyzeMessage: (payload: {
    message: string;
    sender_id?: string | null;
    qr_payloads?: string[];
    source?: "text" | "ocr" | "example";
    model_name?: "logistic_regression" | "multinomial_nb";
    threshold?: number;
    save_to_history?: boolean;
  }) =>
    requestJson<AnalyzeResponse>("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  extractScreenshotText: async (file: File): Promise<OCRResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    return requestJson<OCRResponse>("/api/ocr/extract", {
      method: "POST",
      body: formData,
    });
  },

  getHistory: (search = "", category = "All") => {
    const params = new URLSearchParams();
    if (search.trim()) params.set("search", search.trim());
    if (category && category !== "All") params.set("category", category);
    return requestJson<HistoryListResponse>(`/api/history?${params.toString()}`);
  },

  deleteHistoryItem: (id: number) =>
    requestJson<{ deleted: boolean }>(`/api/history/${id}`, { method: "DELETE" }),

  clearHistory: () =>
    requestJson<{ deleted_count: number }>("/api/history", { method: "DELETE" }),

  getModelInsights: () => requestJson<ModelInsightsResponse>("/api/model/insights"),

  inspectBatchCsv: async (file: File): Promise<BatchInspectResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    return requestJson<BatchInspectResponse>("/api/batch/inspect", {
      method: "POST",
      body: formData,
    });
  },

  analyzeBatchCsv: async (file: File, textColumn: string): Promise<BatchAnalyzeResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("text_column", textColumn);
    return requestJson<BatchAnalyzeResponse>("/api/batch/analyze", {
      method: "POST",
      body: formData,
    });
  },

  runBundledDemoBatch: () =>
    requestJson<BatchAnalyzeResponse>("/api/batch/demo", { method: "POST" }),

  exportBatchCsv: async (results: BatchRowResult[]): Promise<Blob> => {
    const response = await fetch("/api/batch/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(results),
    });
    if (!response.ok) {
      throw new Error("Could not export analyzed CSV.");
    }
    return await response.blob();
  },

  getSettings: () => requestJson<SettingsModel>("/api/settings"),

  updateSettings: (patch: Partial<SettingsModel>) =>
    requestJson<SettingsModel>("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }),
};
