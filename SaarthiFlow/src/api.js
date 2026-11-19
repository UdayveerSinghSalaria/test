// Reusable API Client for SaarthiFlow
const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '/api' : '');

function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(endpoint, options = {}) {
  if (!API_BASE) {
    throw new Error('Production API is not configured. Set VITE_API_URL to the deployed backend URL ending in /api.');
  }
  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...getAuthHeaders(),
      ...(options.headers || {})
    }
  };

  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
    config.body = JSON.stringify(config.body);
  }

  let res;
  try {
    res = await fetch(url, config);
  } catch (networkErr) {
    throw new Error(`Cannot connect to SaarthiFlow backend at ${API_BASE}. Ensure the backend server is running.`);
  }

  const contentType = res.headers.get('content-type') || '';
  let data;
  try {
    if (contentType.includes('application/json')) {
      data = await res.json();
    } else {
      const text = await res.text();
      if (!res.ok) {
        throw new Error(`Server returned non-JSON response (${res.status}): ${text.slice(0, 200)}`);
      }
      data = null;
    }
  } catch (parseErr) {
    if (!res.ok) {
      throw new Error(`Server error (${res.status}): ${parseErr.message}`);
    }
    data = null;
  }

  if (!res.ok) {
    const errorMsg = data?.detail || data?.error || data?.message || `API request failed with status ${res.status}`;
    const err = new Error(errorMsg);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

export const api = {
  // Auth
  register: (data) => request('/auth/register', { method: 'POST', body: data }),
  login: (data) => request('/auth/login', { method: 'POST', body: data }),
  getMe: () => request('/auth/me'),

  // Health
  getHealth: () => request('/health'),

  // Tasks
  getTasks: (params = {}) => {
    const query = new URLSearchParams();
    if (params.status && params.status !== 'All') query.set('status', params.status);
    if (params.priority && params.priority !== 'All') query.set('priority', params.priority);
    if (params.project && params.project !== 'All') query.set('project', params.project);
    const qs = query.toString();
    return request(`/tasks${qs ? `?${qs}` : ''}`);
  },
  createTask: (task) => request('/tasks', { method: 'POST', body: task }),
  updateTask: (id, patch) => request(`/tasks/${id}`, { method: 'PATCH', body: patch }),
  deleteTask: (id) => request(`/tasks/${id}`, { method: 'DELETE' }),
  toggleTask: (id) => request(`/tasks/${id}/toggle`, { method: 'POST' }),

  // Projects
  getProjects: () => request('/projects'),
  createProject: (name) => request('/projects', { method: 'POST', body: { name } }),

  // Agent Planning & Runs
  generatePlan: ({ command, webpageUrl, webpageText }) =>
    request('/agent/plan', {
      method: 'POST',
      body: { command, webpageUrl, webpageText }
    }),
  getAgentRuns: () => request('/agent/runs'),

  // Action Proposals & Approvals
  getApprovals: (status) => {
    const qs = status && status !== 'All' ? `?status=${encodeURIComponent(status)}` : '';
    return request(`/approvals${qs}`);
  },
  updateProposal: (id, patch) => request(`/approvals/${id}`, { method: 'PATCH', body: patch }),
  approveProposal: (id, tasks) =>
    request(`/approvals/${id}/approve`, {
      method: 'POST',
      body: { tasks }
    }),
  rejectProposal: (id) =>
    request(`/approvals/${id}/reject`, {
      method: 'POST'
    }),

  // Activity Logs
  getActivity: (params = {}) => {
    const query = new URLSearchParams();
    if (params.status && params.status !== 'All') query.set('status', params.status);
    const qs = query.toString();
    return request(`/activity${qs ? `?${qs}` : ''}`);
  },

  // Analytics
  getAnalytics: () => request('/analytics'),

  // Settings
  getSettings: () => request('/settings'),
  saveSettings: (settings) => request('/settings', { method: 'POST', body: settings }),

  // Email Accounts
  getEmailAccounts: () => request('/emails/accounts'),
  addEmailAccount: (data) => request('/emails/accounts', { method: 'POST', body: data }),
  deleteEmailAccount: (id) => request(`/emails/accounts/${id}`, { method: 'DELETE' }),
  fetchEmails: (params) => request('/emails/fetch', { method: 'POST', body: params }),
  sendEmail: (data) => request('/emails/send', { method: 'POST', body: data }),
};