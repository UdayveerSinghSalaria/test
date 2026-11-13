"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2,
  Circle,
  ListTodo,
  Loader2,
  Plus,
  Trash2,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiDelete, apiGet, apiPatch, apiPost, ApiError } from "@/lib/api";
import type { Task } from "@/types";

const PRIORITY_VARIANT: Record<Task["priority"], "default" | "secondary" | "outline"> = {
  high: "default",
  medium: "secondary",
  low: "outline",
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<"all" | "pending" | "completed">("all");
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const rows = await apiGet<Task[]>(
        filter === "all" ? "/api/tasks" : `/api/tasks?status=${filter}`
      );
      setTasks(rows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks.");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  const addTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy(true);
    try {
      await apiPost<Task>("/api/tasks", { title: title.trim() });
      setTitle("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create task.");
    } finally {
      setBusy(false);
    }
  };

  const toggleStatus = async (task: Task) => {
    const next =
      task.status === "completed" ? "pending" : "completed";
    setTasks((prev) =>
      prev.map((t) => (t.id === task.id ? { ...t, status: next } : t))
    );
    try {
      await apiPatch<Task>(`/api/tasks/${task.id}`, { status: next });
    } catch {
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: task.status } : t))
      );
      setError("Could not update the task.");
    }
  };

  const remove = async (task: Task) => {
    setTasks((prev) => prev.filter((t) => t.id !== task.id));
    try {
      await apiDelete(`/api/tasks/${task.id}`);
    } catch {
      setError("Could not delete the task.");
      await load();
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-5 px-4 py-6 md:px-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">My Tasks</h1>
            <p className="text-sm text-muted-foreground">
              Everything you and the assistant have queued up.
            </p>
          </div>
          <Tabs value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
            <TabsList>
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="pending">Pending</TabsTrigger>
              <TabsTrigger value="completed">Done</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <form onSubmit={addTask} className="flex gap-2">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Add a task…"
            className="flex-1"
          />
          <Button type="submit" disabled={busy || !title.trim()}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
            Add
          </Button>
        </form>

        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="space-y-3 p-4">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-8 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : tasks.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-12 text-center">
                <ListTodo className="size-8 text-muted-foreground/50" />
                <p className="text-sm text-muted-foreground">
                  {filter === "completed"
                    ? "Nothing completed yet."
                    : "No tasks here. Add one or ask the assistant."}
                </p>
              </div>
            ) : (
              <ul>
                {tasks.map((task) => (
                  <li
                    key={task.id}
                    className="group flex items-center gap-3 border-b border-border px-4 py-3 last:border-b-0"
                  >
                    <button
                      type="button"
                      onClick={() => toggleStatus(task)}
                      aria-label="Toggle completion"
                      className="shrink-0"
                    >
                      {task.status === "completed" ? (
                        <CheckCircle2 className="size-4.5 text-emerald-500" />
                      ) : (
                        <Circle className="size-4.5 text-muted-foreground hover:text-foreground" />
                      )}
                    </button>
                    <div className="min-w-0 flex-1">
                      <p
                        className={`text-sm ${
                          task.status === "completed"
                            ? "text-muted-foreground line-through"
                            : "text-foreground"
                        }`}
                      >
                        {task.title}
                      </p>
                      <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <Badge
                          variant={PRIORITY_VARIANT[task.priority]}
                          className="text-[10px] uppercase"
                        >
                          {task.priority}
                        </Badge>
                        {task.due_date && (
                          <span>
                            due {new Date(task.due_date).toLocaleDateString()}
                          </span>
                        )}
                        {task.source === "agent" && (
                          <span className="text-muted-foreground/70">
                            created by assistant
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="opacity-0 transition-opacity group-hover:opacity-100"
                      onClick={() => remove(task)}
                      aria-label="Delete task"
                    >
                      <Trash2 className="size-4 text-muted-foreground" />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
