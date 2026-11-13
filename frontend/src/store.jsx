import React, { createContext, useContext, useEffect, useState } from 'react';
import api from './api';

const C = createContext();
export const useApp = () => useContext(C);

export const uid = () => Math.random().toString(36).slice(2, 9);
export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export const fmtD = d => { if (!d) return 'No date'; const [, m, day] = d.split('-'); return MONTHS[+m - 1] + ' ' + +day };
export const iso = (y, m, d) => `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
export const TODAY = (() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}` })();

function mapTask(t) {
  return {
    id: t.id,
    title: t.title,
    project: t.project || 'General',
    priority: (t.priority || 'medium').charAt(0).toUpperCase() + (t.priority || 'medium').slice(1),
    status: ({ pending: 'todo', in_progress: 'doing', completed: 'done' })[t.status] || t.status || 'todo',
    due: t.due_date ? String(t.due_date).slice(0, 10) : '',
  };
}

function mapProposal(p) {
  const payload = p.payload || {};
  const tasks = Array.isArray(p.tasks)
    ? p.tasks
    : (p.action === 'create_task' ? [{ ...payload, id: p.id }] : []);
  return {
    id: p.id,
    title: p.title || payload.title || p.action || 'Proposed action',
    source: p.source || 'Agent',
    created: p.created_at,
    status: p.status,
    tasks: tasks.map(mapTask),
    decided_at: p.decided_at || p.resolved_at,
  };
}

function mapActivity(a) {
  return {
    id: a.id,
    at: a.at || a.created_at,
    type: a.type || a.kind,
    title: a.title || a.action,
    detail: a.detail,
    source: a.source,
    status: a.status,
  };
}

function mapSettings(s) {
  return {
    name: s.name || 'User',
    email: s.email || '',
    role: s.role || '',
    weekStart: s.week_start || 'Mon',
    notify: s.notify ?? true,
  };
}

function mapProposalCreate(p) {
  return {
    title: p.title,
    source: p.source,
    tasks: p.tasks.map(t => ({
      title: t.title,
      project: t.project,
      priority: t.priority,
      due: t.due,
    })),
  };
}

export function Store({ children }) {
  const [s, set] = useState({
    tasks: [],
    proposals: [],
    activity: [],
    settings: { name: 'User', email: '', role: '', weekStart: 'Mon', notify: true },
    loading: true,
    error: null,
    authRequired: false,
  });

  const loadAll = async () => {
    set(s => ({ ...s, loading: true, error: null }));
    try {
      const settings = await api.me();
      const [tasks, proposals, activity] = await Promise.all([
        api.getTasks(),
        api.getApprovals(),
        api.getActivity(),
      ]);
      set(s => ({
        ...s,
        tasks: tasks.map(mapTask),
        proposals: proposals.map(mapProposal),
        activity: activity.map(mapActivity),
        settings: mapSettings(settings),
        loading: false,
        authRequired: false,
        error: null,
      }));
    } catch (err) {
      set(s => ({
        ...s,
        loading: false,
        authRequired: err.status === 401,
        error: err.status === 401 ? null : err.message,
      }));
    }
  };

  useEffect(() => { loadAll(); }, []);

  const log = (a, type, title, detail, source, status = 'Completed') => ({
    ...a,
    activity: [{ id: uid(), at: Date.now(), type, title, detail, source, status }, ...a.activity],
  });

  const refreshAll = async () => {
    await loadAll();
  };

  const apiWrapper = {
    ...s,
    signIn: async (email, password) => {
      await api.login(email, password);
      await loadAll();
    },
    signUp: async (email, password, name) => {
      await api.signup(email, password, name);
      await loadAll();
    },
    addTask: async (t) => {
      const newTask = await api.createTask({
        title: t.title,
        description: t.description || '',
        project: t.project || 'General',
        priority: t.priority || 'Medium',
        status: t.status || 'todo',
        due_date: t.due || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      });
      set(a => log({ ...a, tasks: [mapTask(newTask), ...a.tasks] }, 'Task', 'Task created: ' + newTask.title, newTask.project + ' · due ' + fmtD(newTask.due_date), 'My Space'));
    },
    updateTask: async (t) => {
      const updated = await api.updateTask(t.id, {
        title: t.title,
        project: t.project,
        priority: t.priority,
        status: t.status,
        due_date: t.due,
      });
      set(a => log({ ...a, tasks: a.tasks.map(x => x.id === t.id ? mapTask(updated) : x) }, 'Task', 'Task updated: ' + updated.title, 'Status: ' + updated.status, 'My Space'));
    },
    deleteTask: async (id) => {
      await api.deleteTask(id);
      set(a => { const t = a.tasks.find(x => x.id === id); return log({ ...a, tasks: a.tasks.filter(x => x.id !== id) }, 'Task', 'Task deleted: ' + t?.title, 'Removed from My Space', 'My Space', 'Cancelled'); });
    },
    toggleTask: async (id) => {
      const t = s.tasks.find(x => x.id === id);
      const newStatus = t.status === 'done' ? 'todo' : 'done';
      const updated = await api.toggleTask(id);
      set(a => log({ ...a, tasks: a.tasks.map(x => x.id === id ? { ...x, status: newStatus } : x) }, 'Task', (newStatus === 'done' ? 'Completed: ' : 'Reopened: ') + t.title, 'Status changed', 'My Space'));
    },
    addProposal: async (p) => {
      const proposal = await api.createApproval(mapProposalCreate(p));
      set(a => log({ ...a, proposals: [mapProposal(proposal), ...a.proposals] }, 'Plan', 'Plan sent for approval: ' + proposal.title, proposal.tasks.length + ' proposed tasks', 'Agent Studio', 'Pending'));
    },
    decide: async (id, ok, tasks) => {
      const decision = { approved: ok, tasks: tasks ? tasks.map(mapProposalCreate) : undefined };
      await api.decideApproval(id, decision);
      const p = s.proposals.find(x => x.id === id);
      if (!p || p.status !== 'pending') return;
      const list = tasks || p.tasks;
      const np = { ...p, tasks: list, status: ok ? 'approved' : 'rejected', decided_at: Date.now() };
      const nt = ok ? list.map(t => ({ ...t, id: uid(), status: 'todo' })) : [];
      set(a => log({ ...a, proposals: a.proposals.map(x => x.id === id ? np : x), tasks: [...nt.map(mapTask), ...a.tasks] }, 'Approval', (ok ? 'Approved: ' : 'Rejected: ') + p.title, ok ? nt.length + ' tasks created in My Space' : 'No tasks created', 'Approvals', ok ? 'Completed' : 'Rejected'));
    },
    logOnly: (type, title, detail, source) => set(a => log(a, type, title, detail, source)),
    saveSettings: async (v) => {
      await api.saveSettings(v);
      set(a => log({ ...a, settings: v }, 'Settings', 'Settings saved', 'Preferences updated', 'Settings'));
    },
    reset: async () => {
      // Reset would require backend support
      localStorage.removeItem('sf-v1');
      location.reload();
    },
    refreshAll,
  };

  return <C.Provider value={apiWrapper}>{children}</C.Provider>;
}