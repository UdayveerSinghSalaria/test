/**
 * Centralized API client.
 *
 * All requests go to the Next.js /api proxy (same-origin), which forwards to
 * FastAPI. The session cookie is httpOnly and sent automatically; nothing
 * auth-related is ever stored in localStorage.
 */

import { API_BASE } from "./config";
import type {
  Task,
  TaskCreate,
  TaskUpdate,
  Proposal,
  ProposalCreate,
  ProposalDecide,
  ActivityEntry,
  UserSettings,
} from "@/types";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail
        .map((d: { msg?: string; loc?: unknown }) => d.msg ?? JSON.stringify(d))
        .join("; ");
    }
    return `Request failed (HTTP ${res.status})`;
  } catch {
    return `Request failed (HTTP ${res.status})`;
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });

  if (!res.ok) {
    throw new ApiError(res.status, await parseError(res));
  }
  if (res.status === 204) {
    return undefined as T;
  }
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export const apiGet = <T>(path: string) => api<T>(path);

export const apiPost = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const apiPatch = <T>(path: string, body: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body) });

export const apiDelete = <T>(path: string) => api<T>(path, { method: "DELETE" });

/**
 * POST + read an NDJSON event stream (the agent runner).
 * Yields one parsed event per line so the UI can render progress live.
 */
export async function* apiStream(
  path: string,
  body: unknown,
  signal?: AbortSignal
): AsyncGenerator<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok || !res.body) {
    throw new ApiError(res.status, await parseError(res));
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        yield JSON.parse(trimmed);
      } catch {
        // partial/garbled line — skip, keep streaming
      }
    }
  }
}

// ===== Tasks =====
export const getTasks = () => apiGet<Task[]>("/api/tasks");
export const createTask = (body: TaskCreate) => apiPost<Task>("/api/tasks", body);
export const updateTask = (id: string, body: TaskUpdate) => apiPatch<Task>(`/api/tasks/${id}`, body);
export const deleteTask = (id: string) => apiDelete<void>(`/api/tasks/${id}`);
export const toggleTask = (id: string) => apiPatch<Task>(`/api/tasks/${id}/toggle`, {});

// ===== Approvals =====
export const getApprovals = () => apiGet<Proposal[]>("/api/approvals");
export const createApproval = (body: ProposalCreate) => apiPost<Proposal>("/api/approvals", body);
export const decideApproval = (id: string, body: ProposalDecide) => apiPatch<Proposal>(`/api/approvals/${id}`, body);

// ===== Activity =====
export const getActivity = () => apiGet<ActivityEntry[]>("/api/activity");

// ===== Settings =====
export const getSettings = () => apiGet<UserSettings>("/api/auth/me");
export const updateSettings = (body: Partial<UserSettings>) => apiPatch<UserSettings>("/api/auth/me", body);

// ===== Agent =====
export const streamAgent = (body: { prompt: string }, signal?: AbortSignal) =>
  apiStream("/api/assistant", body, signal);
