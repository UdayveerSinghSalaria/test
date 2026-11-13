/** Shared types mirroring the FastAPI Pydantic schemas. */

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface Integration {
  provider: string;
  provider_email: string;
  scopes: string[];
  connected_at: string;
  token_expiry: string | null;
  status: string;
}

export interface EmailSummary {
  id: string;
  thread_id: string;
  sender_name: string;
  sender_email: string;
  subject: string;
  snippet: string;
  received_at: string | null;
  is_unread: boolean;
}

export interface EmailListResponse {
  emails: EmailSummary[];
  next_page_token: string | null;
}

export interface EmailAddress {
  name: string;
  address: string;
}

export interface EmailDetail extends EmailSummary {
  to: EmailAddress[];
  body_text: string;
  body_html_sanitized: string;
  label_ids: string[];
  attachments: string[];
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: "pending" | "in_progress" | "completed";
  priority: "low" | "medium" | "high";
  due_date: string | null;
  source: string;
  created_at: string;
}

export interface Approval {
  id: string;
  action: string;
  payload: Record<string, unknown>;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}

export interface Activity {
  id: string;
  kind: "tool_call" | "plan" | "approval" | "error" | "info";
  action: string;
  status: string;
  detail: string;
  created_at: string;
}

/** One streamed event from the agent run (assistant page). */
export interface AgentStep {
  type: "plan" | "tool_start" | "tool_result" | "approval_required" | "answer" | "error";
  text: string;
  tool: string;
  detail: string;
  approval_id: string | null;
}

export interface Health {
  status: string;
  app_name: string;
  llm_configured: boolean;
  google_oauth_configured: boolean;
}
