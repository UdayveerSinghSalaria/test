/** TypeScript types mirroring FastAPI Pydantic schemas */

export interface Task {
  id: string;
  title: string;
  description?: string;
  project: string;
  priority: "High" | "Medium" | "Low";
  status: "todo" | "doing" | "done";
  due_date: string;
  source: "agent" | "manual";
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  project?: string;
  priority?: "High" | "Medium" | "Low";
  status?: "todo" | "doing" | "done";
  due_date?: string;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  project?: string;
  priority?: "High" | "Medium" | "Low";
  status?: "todo" | "doing" | "done";
  due_date?: string;
}

export interface ProposalTask {
  id: string;
  title: string;
  project: string;
  priority: "High" | "Medium" | "Low";
  due: string;
}

export interface Proposal {
  id: string;
  title: string;
  source: string;
  created: number;
  status: "pending" | "approved" | "rejected";
  tasks: ProposalTask[];
  decided_at?: number;
}

export interface ProposalCreate {
  title: string;
  source: string;
  tasks: ProposalTask[];
}

export interface ProposalDecide {
  approved: boolean;
  tasks?: ProposalTask[];
}

export interface ActivityEntry {
  id: string;
  at: number;
  type: string;
  title: string;
  detail: string;
  source: string;
  status: "Completed" | "Pending" | "Rejected" | "Cancelled";
}

export interface UserSettings {
  name: string;
  email: string;
  role: string;
  week_start: "Mon" | "Sun";
  notify: boolean;
}

export interface EmailSummary {
  id: string;
  thread_id: string;
  subject: string;
  from_email: string;
  to_email: string;
  date: string;
  snippet: string;
  is_unread: boolean;
  labels: string[];
}

export interface EmailListResponse {
  emails: EmailSummary[];
  next_page_token?: string;
}

export interface EmailDetail {
  id: string;
  thread_id: string;
  subject: string;
  from_email: string;
  to_email: string;
  date: string;
  body_text: string;
  body_html: string;
  attachments: Array<{
    id: string;
    filename: string;
    mime_type: string;
    size: number;
  }>;
  message_id: string;
  labels: string[];
}

export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_page_token?: string;
}