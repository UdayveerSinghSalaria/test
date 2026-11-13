"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import type { Task, TaskCreate, TaskUpdate, Proposal, ProposalCreate, ProposalDecide, ActivityEntry, UserSettings } from "@/types";
import {
  getTasks,
  createTask,
  updateTask,
  deleteTask,
  toggleTask,
  getApprovals,
  createApproval,
  decideApproval,
  getActivity,
  getSettings,
  updateSettings,
} from "@/lib/api";

interface AppState {
  tasks: Task[];
  proposals: Proposal[];
  activity: ActivityEntry[];
  settings: UserSettings | null;
  loading: boolean;
  error: string | null;
}

interface AppActions {
  // Tasks
  fetchTasks: () => Promise<void>;
  addTask: (task: TaskCreate) => Promise<Task>;
  updateTask: (id: string, updates: TaskUpdate) => Promise<void>;
  deleteTask: (id: string) => Promise<void>;
  toggleTask: (id: string) => Promise<void>;

  // Proposals
  fetchApprovals: () => Promise<void>;
  addProposal: (proposal: ProposalCreate) => Promise<Proposal>;
  decideProposal: (id: string, decision: ProposalDecide) => Promise<void>;

  // Activity
  fetchActivity: () => Promise<void>;

  // Settings
  fetchSettings: () => Promise<void>;
  saveSettings: (settings: Partial<UserSettings>) => Promise<void>;

  // State
  loading: boolean;
  error: string | null;
}

const AppContext = createContext<AppState & AppActions | null>(null);

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AppState>({
    tasks: [],
    proposals: [],
    activity: [],
    settings: null,
    loading: true,
    error: null,
  });

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  // --- Tasks ---
  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      const tasks = await getTasks();
      setState(prev => ({ ...prev, tasks, loading: false }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks");
      setLoading(false);
    }
  }, [setLoading, setError]);

  const addTask = useCallback(async (task: TaskCreate) => {
    const newTask = await createTask(task);
    setState(prev => ({ ...prev, tasks: [newTask, ...prev.tasks] }));
    return newTask;
  }, []);

  const updateTask = useCallback(async (id: string, updates: TaskUpdate) => {
    const updated = await updateTask(id, updates);
    setState(prev => ({
      ...prev,
      tasks: prev.tasks.map(t => t.id === id ? updated : t),
    }));
  }, []);

  const deleteTask = useCallback(async (id: string) => {
    await deleteTask(id);
    setState(prev => ({ ...prev, tasks: prev.tasks.filter(t => t.id !== id) }));
  }, []);

  const toggleTask = useCallback(async (id: string) => {
    const updated = await toggleTask(id);
    setState(prev => ({
      ...prev,
      tasks: prev.tasks.map(t => t.id === id ? updated : t),
    }));
  }, []);

  // --- Proposals ---
  const fetchApprovals = useCallback(async () => {
    try {
      const proposals = await getApprovals();
      setState(prev => ({ ...prev, proposals }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load approvals");
    }
  }, [setError]);

  const addProposal = useCallback(async (proposal: ProposalCreate) => {
    const newProposal = await createApproval(proposal);
    setState(prev => ({ ...prev, proposals: [newProposal, ...prev.proposals] }));
    return newProposal;
  }, []);

  const decideProposal = useCallback(async (id: string, decision: ProposalDecide) => {
    const updated = await decideApproval(id, decision);
    setState(prev => ({
      ...prev,
      proposals: prev.proposals.map(p => p.id === id ? updated : p),
      tasks: decision.approved && decision.tasks
        ? [...decision.tasks.map(t => ({ ...t, id: crypto.randomUUID() })), ...prev.tasks]
        : prev.tasks,
    }));
  }, []);

  // --- Activity ---
  const fetchActivity = useCallback(async () => {
    try {
      const activity = await getActivity();
      setState(prev => ({ ...prev, activity }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load activity");
    }
  }, [setError]);

  // --- Settings ---
  const fetchSettings = useCallback(async () => {
    try {
      const settings = await getSettings();
      setState(prev => ({ ...prev, settings }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    }
  }, [setError]);

  const saveSettings = useCallback(async (settings: Partial<UserSettings>) => {
    const updated = await updateSettings(settings);
    setState(prev => ({ ...prev, settings: updated }));
  }, []);

  // Initial load
  useEffect(() => {
    Promise.all([
      fetchTasks(),
      fetchApprovals(),
      fetchActivity(),
      fetchSettings(),
    ]).finally(() => setLoading(false));
  }, [fetchTasks, fetchApprovals, fetchActivity, fetchSettings, setLoading]);

  return (
    <AppContext.Provider value={{ ...state, ...{
      fetchTasks,
      addTask,
      updateTask,
      deleteTask,
      toggleTask,
      fetchApprovals,
      addProposal,
      decideProposal,
      fetchActivity,
      fetchSettings,
      saveSettings,
      loading: state.loading,
      error: state.error,
    } }}>
      {children}
    </AppContext.Provider>
  );
}