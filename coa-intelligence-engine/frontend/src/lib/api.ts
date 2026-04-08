import type {
  ApiResponse,
  CoAResult,
  StatusResponse,
  SubmissionSummary,
  UploadResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const url = `${API_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const error =
      body?.detail?.error ??
      body?.error ?? {
        code: `HTTP_${response.status}`,
        message: response.statusText,
      };
    return { data: null, error };
  }

  const body = await response.json();
  return body as ApiResponse<T>;
}

// ─── CoA endpoints ────────────────────────────────────────────────────────────

export async function uploadCoA(file: File): Promise<ApiResponse<UploadResponse>> {
  const formData = new FormData();
  formData.append("file", file);

  return request<UploadResponse>("/api/coa/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getCoAStatus(submissionId: string): Promise<ApiResponse<StatusResponse>> {
  return request<StatusResponse>(`/api/coa/status/${submissionId}`);
}

export async function getCoAResult(submissionId: string): Promise<ApiResponse<CoAResult>> {
  return request<CoAResult>(`/api/coa/result/${submissionId}`);
}

export function getExportUrl(submissionId: string, format: "csv" | "json"): string {
  return `${API_URL}/api/coa/export/${submissionId}?format=${format}`;
}

export async function listSubmissions(limit = 20): Promise<ApiResponse<SubmissionSummary[]>> {
  return request<SubmissionSummary[]>(`/api/coa/submissions?limit=${limit}`);
}
