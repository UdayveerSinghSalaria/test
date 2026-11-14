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
  createApproval: (proposal) => apiRequest('/approvals', { method: 'POST', body: JSON.stringify(proposal) }),
  decideApproval: (id, decision) => apiRequest(`/approvals/${id}`, { method: 'PATCH', body: JSON.stringify(decision) }),

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