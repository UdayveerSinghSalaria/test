"use client";

import React, { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ClipboardList, CheckCircle2, CalendarClock, Sparkles, Paperclip, Globe, CalendarDays, ListChecks, Plus, ArrowUpRight, Trash2, Pencil, ChevronLeft, ChevronRight, Send, Check, X, Download, Search, Trophy, Activity as ActI, BarChart3, Bot, Circle, Loader2, Zap, Shield, MousePointerClick } from "lucide-react";
import { useApp } from "@/context/app-context";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Title, Badge, Page, Empty, TaskModal } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const fmtD = (d: string) => {
  if (!d) return "No date";
  const [, m, day] = d.split("-");
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return MONTHS[+m - 1] + " " + +day;
};

export default function SpacePage() {
  return (
    <Suspense fallback={<div className="flex h-[400px] items-center justify-center">Loading…</div>}>
      <SpacePageContent />
    </Suspense>
  );
}

function SpacePageContent() {
  const { tasks, addTask, updateTask, deleteTask, toggleTask } = useApp();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [q, setQ] = useState(searchParams.get("q") || "");
  const [view, setView] = useState("list");
  const [pf, setPf] = useState("All");
  const [sf, setSf] = useState("All");
  const [m, setM] = useState<null | { id?: string }>(null);

  React.useEffect(() => { setQ(searchParams.get("q") || "") }, [searchParams]);

  const list = tasks.filter(t => (t.title + t.project).toLowerCase().includes(q.toLowerCase()) && (pf === "All" || t.priority === pf) && (sf === "All" || t.status === sf)).sort((a, b) => a.due_date.localeCompare(b.due_date));

  const projects = useMemo(() => {
    const o: Record<string, { n: number; d: number }> = {};
    tasks.forEach(t => { o[t.project] = o[t.project] || { n: 0, d: 0 }; o[t.project].n++; if (t.status === "done") o[t.project].d++; });
    return Object.entries(o);
  }, [tasks]);

  const statusLabels: Record<string, string> = { todo: "To do", doing: "In progress", done: "Done" };

  const Row = (t: any) => (
    <div key={t.id} className="glass hov flex flex-wrap items-center gap-3 rounded-2xl p-3" onClick={() => setM(t)}>
      <CheckToggle checked={t.status === "done"} onChange={() => toggleTask(t.id)} />
      <div className="min-w-0 flex-1">
        <div className={`truncate font-semibold ${t.status === "done" ? "line-through text-ink/45" : ""}`}>{t.title}</div>
        <div className="text-xs text-ink/55">{t.project} · due {fmtD(t.due_date)}</div>
      </div>
      <Badge variant={t.priority.toLowerCase() as "high" | "medium" | "low"}>{t.priority}</Badge>
      <span className="chip bg-brand-100 text-brand-700">{statusLabels[t.status]}</span>
      <button onClick={e => { e.stopPropagation(); setM(t) }} aria-label="Edit"><Pencil size={16} /></button>
      <button onClick={e => { e.stopPropagation(); deleteTask(t.id) }} aria-label="Delete" className="text-rose-500"><Trash2 size={16} /></button>
    </div>
  );

  const handleCloseModal = () => setM(null);
  const handleSaveTask = (taskData: any) => {
    if (taskData.id) {
      updateTask(taskData.id, taskData);
    } else {
      addTask(taskData);
    }
  };

  return (
    <AppShell>
      <Page title="My Space" sub="All your tasks and projects in one place." right={<Button onClick={() => setM({})}><Plus size={16} />New task</Button>}>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {projects.slice(0, 4).map(([p, v]) => (
            <Card key={p} className="hov p-4">
              <b>{p}</b>
              <div className="mt-2 h-2 rounded-full bg-brand-100"><div className="h-2 rounded-full bg-brand-500" style={{ width: v.d / v.n * 100 + "%" }} /></div>
              <div className="mt-1 text-xs text-ink/60">{v.d}/{v.n} done</div>
            </Card>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="glass rounded-xl flex flex-1 items-center gap-2 px-3">
            <Search size={16} />
            <Input value={q} onChange={e => setQ(e.target.value)} placeholder="Search tasks or projects" className="w-full min-w-[140px] bg-transparent py-2 text-sm outline-none" />
          </div>
          <Select value={pf} onChange={e => setPf(e.target.value)} options={[{ value: "All", label: "All priorities" }, { value: "High", label: "High" }, { value: "Medium", label: "Medium" }, { value: "Low", label: "Low" }]} className="inp w-auto" />
          <Select value={sf} onChange={e => setSf(e.target.value)} options={[{ value: "All", label: "All statuses" }, { value: "todo", label: "To do" }, { value: "doing", label: "In progress" }, { value: "done", label: "Done" }]} className="inp w-auto" />
          <div className="glass rounded-xl flex p-1">
            {["list", "kanban"].map(v => (
              <Button key={v} variant={view === v ? "primary" : "secondary"} size="sm" onClick={() => setView(v)}>
                {v === "list" ? "Task List" : "Kanban"}
              </Button>
            ))}
          </div>
        </div>
        {view === "list" ? (
          <div className="space-y-2">
            {list.map(Row)}
            {!list.length && <Empty text="No tasks match. Create one with New task." />}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["todo", "To do"],
              ["doing", "In progress"],
              ["done", "Done"],
            ].map(([s, l]) => (
              <Card key={s} className="p-4">
                <h4 className="mb-3 font-bold">{l} <span className="text-ink/45">({list.filter(t => t.status === s).length})</span></h4>
                <div className="space-y-2">
                  {list.filter(t => t.status === s).map(t => (
                    <div key={t.id} className="rounded-2xl bg-white/80 p-3 text-sm">
                      <div className="font-semibold">{t.title}</div>
                      <div className="mt-1 flex items-center gap-2 text-xs text-ink/55">
                        <Badge variant={t.priority.toLowerCase() as "high" | "medium" | "low"}>{t.priority}</Badge>
                        {fmtD(t.due_date)}
                      </div>
                      <div className="mt-2 flex items-center gap-2">
                        <Select value={t.status} onChange={v => updateTask(t.id, { ...t, status: v })} options={[{ value: "todo", label: "To do" }, { value: "doing", label: "In progress" }, { value: "done", label: "Done" }]} className="inp py-1 text-xs" />
                        <button onClick={() => setM(t)} aria-label="Edit"><Pencil size={14} /></button>
                        <button className="text-rose-500" onClick={() => deleteTask(t.id)} aria-label="Delete"><Trash2 size={14} /></button>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        )}
        <TaskModal isOpen={!!m} onClose={() => setM(null)} task={m || undefined} onSave={t => t.id ? updateTask(t.id, t) : addTask(t)} />
      </Page>
    </AppShell>
  );
}

function Select({ value, onChange, options, className = "" }: { value: string; onChange: (v: string) => void; options: { value: string; label: string }[]; className?: string }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)} className={`rounded-xl border border-brand-200 bg-white/80 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 dark:bg-white/10 dark:border-brand-800 ${className}`}>
      {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
    </select>
  );
}

function CheckToggle({ checked, onChange }: { checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <button onClick={() => onChange(!checked)} className={`grid h-6 w-6 shrink-0 place-items-center rounded-md border-2 transition ${checked ? "border-brand-600 bg-brand-600 text-white" : "border-brand-200 bg-white hover:border-brand-500"}`}>
      {checked && <Check size={14} />}
    </button>
  );
}