// API client for backend integration
const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? 'http://localhost:8000/api' : '/api')
).replace(/\/+$/, '');

async function apiRequest(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    const error = new Error(err.detail || `Request failed (${res.status})`);
    error.status = res.status;
    throw error;
  }
  if (res.status === 204) return undefined;
  const text = await res.text();
  return text ? JSON.parse(text) : undefined;
}

async function streamRequest(path, payload, onEvent) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  if (!res.body) throw new Error('The assistant response stream is unavailable.');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let receivedEvent = false;
  let completed = false;
  const dispatch = line => {
    const event = JSON.parse(line);
    receivedEvent = true;
    if (['answer', 'error', 'approval_required'].includes(event.type)) completed = true;
    onEvent(event);
  };
  const emitLines = () => {
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    lines.forEach(line => {
      if (line.trim()) dispatch(line);
    });
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    emitLines();
    if (done) break;
  }
  if (buffer.trim()) dispatch(buffer);
  if (!receivedEvent) throw new Error('The assistant returned an empty response. Check the backend deployment and logs.');
  if (!completed) throw new Error('The assistant stream ended before returning a result. Please try again.');
}

export const api = {
  // Auth
  login: (email, password) => apiRequest('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  signup: (email, password, name) => apiRequest('/auth/signup', { method: 'POST', body: JSON.stringify({ email, password, name }) }),
  logout: () => apiRequest('/auth/logout', { method: 'POST' }),
  me: () => apiRequest('/auth/me'),

  // Tasks
  getTasks: () => apiRequest('/tasks'),
  createTask: (task) => apiRequest('/tasks', { method: 'POST', body: JSON.stringify(task) }),
  updateTask: (id, task) => apiRequest(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(task) }),
  deleteTask: (id) => apiRequest(`/tasks/${id}`, { method: 'DELETE' }),
  toggleTask: (id) => apiRequest(`/tasks/${id}/toggle`, { method: 'PATCH' }),

  // Approvals
  getApprovals: () => apiRequest('/approvals?status=all'),
  decideApproval: (id, decision) => apiRequest(`/approvals/${id}/${decision.approved ? 'approve' : 'reject'}`, { method: 'POST' }),

  // Agent
  streamAssistant: (message, onEvent) => streamRequest('/assistant/run', { message }, onEvent),

  // Activity
  getActivity: () => apiRequest('/activity'),

  // User's connected Gmail
  getEmails: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/emails?${qs}`);
  },
  getEmail: (id) => apiRequest(`/emails/${id}`),
  sendEmail: (message) => apiRequest('/emails/send', { method: 'POST', body: JSON.stringify(message) }),

  // Settings
  getSettings: () => apiRequest('/auth/me'),
  saveSettings: (settings) => apiRequest('/auth/me', { method: 'PATCH', body: JSON.stringify(settings) }),

  // Integrations
  googleConnectUrl: () => `${API_BASE}/integrations/google/connect`,
  getGoogleStatus: () => apiRequest('/integrations/google/status'),
  disconnectGoogle: () => apiRequest('/integrations/google', { method: 'DELETE' }),
  getActivepiecesStatus: () => apiRequest('/integrations/activepieces/status'),
};

export default api;