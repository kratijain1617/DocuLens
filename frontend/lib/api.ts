import type { AnswerRecord, CompareResult, DocumentItem, DocumentSummary, EvalItemResult, EvalSummary, User } from "@/lib/types";

function apiBase() {
  const configured = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (configured) return configured;
  // On Vercel the API is the same site, under /api. Locally it stays on port 8000.
  return process.env.NODE_ENV === "production" ? "" : "http://localhost:8000";
}

const BASE = apiBase();

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function detailMessage(payload: unknown) {
  if (!payload || typeof payload !== "object") return "Something went wrong. Please try again.";
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Some of the information sent was not valid. Check the form and try again.";
  return "Something went wrong. Please try again.";
}

export async function api<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    let message = "Something went wrong. Please try again.";
    try {
      message = detailMessage(await response.json());
    } catch {
      message = response.status === 401 ? "Sign in, or start a demo session, to continue." : message;
    }
    throw new ApiError(message, response.status);
  }
  const type = response.headers.get("content-type") || "";
  if (type.includes("application/pdf")) return (await response.blob()) as T;
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const client = {
  signup: (body: { name: string; email: string; password: string; confirm_password: string }) =>
    api<{ token: string; user: User }>("/api/auth/signup", { method: "POST", body: JSON.stringify(body) }),
  login: (body: { email: string; password: string }) =>
    api<{ token: string; user: User }>("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  demo: () => api<{ token: string; user: User }>("/api/auth/demo", { method: "POST" }),
  logout: (token: string) => api<{ ok: boolean }>("/api/auth/logout", { method: "POST" }, token),
  me: (token: string) => api<User>("/api/auth/me", {}, token),
  documents: (token: string) => api<{ documents: DocumentItem[]; categories: string[] }>("/api/documents", {}, token),
  document: (token: string, id: string) => api<DocumentItem>(`/api/documents/${id}`, {}, token),
  file: (token: string, id: string) => api<Blob>(`/api/documents/${id}/file`, {}, token),
  rename: (token: string, id: string, title: string) =>
    api<DocumentItem>(`/api/documents/${id}`, { method: "PATCH", body: JSON.stringify({ title }) }, token),
  remove: (token: string, id: string) => api<{ ok: boolean }>(`/api/documents/${id}`, { method: "DELETE" }, token),
  upload: (token: string, form: FormData) => api<DocumentItem>("/api/documents/upload", { method: "POST", body: form }, token),
  history: (token: string, id: string) => api<{ history: AnswerRecord[] }>(`/api/documents/${id}/history`, {}, token),
  summarize: (token: string, id: string) => api<DocumentSummary>(`/api/documents/${id}/summarize`, { method: "POST" }, token),
  ask: (
    token: string,
    body: {
      document_ids: string[];
      user_question: string;
      conversation_history: { role: string; content: string }[];
      selected_page?: number | null;
      document_category?: string;
    },
  ) => api<AnswerRecord>("/api/ask", { method: "POST", body: JSON.stringify(body) }, token),
  compare: (token: string, body: { document_ids: string[]; user_question: string }) =>
    api<CompareResult>("/api/compare", { method: "POST", body: JSON.stringify(body) }, token),
  dataset: (token: string) => api<{ items: EvalItemResult[]; count: number }>("/api/evaluation/dataset", {}, token),
  evaluate: (token: string) => api<{ summary: EvalSummary; results: EvalItemResult[] }>("/api/evaluation/run", { method: "POST" }, token),
};
