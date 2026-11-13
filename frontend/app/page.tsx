"use client";

import React, { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ClipboardList,
  CheckCircle2,
  CalendarClock,
  Sparkles,
  Paperclip,
  Globe,
  CalendarDays,
  ListChecks,
  Plus,
  ArrowUpRight,
  Trophy,
  Activity as ActI,
  BarChart3,
  Bot,
  Circle,
  Loader2,
  Zap,
  Shield,
  MousePointerClick,
} from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, AreaChart, Area } from "recharts";
import { useApp } from "@/context/app-context";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Title, Badge, Page, Empty } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { TaskModal } from "@/components/ui/task-modal";

const COL = ["#7c3aed", "#b794f6", "#f472b6", "#e4d7ff"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const fmtD = (d: string) => {
  if (!d) return "No date";
  const [, m, day] = d.split("-");
  return MONTHS[+m - 1] + " " + +day;
};
const TODAY = new Date().toISOString().split("T")[0];

const dow = (d: string) => new Date(d + "T00:00:00").getDay();
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const weekly = (tasks: any[]) => [1, 2, 3, 4, 5, 6, 0].map(i => ({ d: DAYS[i], n: tasks.filter(t => dow(t.due_date) === i).length }));
const groups = (a: any[]) => { const c: Record<string, number> = {}; a.forEach(x => c[x.type] = (c[x.type] || 0) + 1); return Object.entries(c).map(([name, value]) => ({ name, value })); };
const tm = (t: number) => new Date(t).toLocaleString("en-IN", { hour: "numeric", minute: "2-digit", day: "numeric", month: "short" });

const Robot = () => (
  <svg viewBox="0 0 120 120" className="h-28 w-28 drop-shadow-xl">
    <circle cx="60" cy="10" r="5" fill="#a78bfa" />
    <path d="M60 14v14" stroke="#a78bfa" strokeWidth="3" />
    <rect x="18" y="28" width="84" height="64" rx="30" fill="#fff" stroke="#d9c8ff" strokeWidth="2" />
    <rect x="28" y="40" width="64" height="40" rx="20" fill="#2a1a5e" />
    <path d="M42 58q6-8 12 0M66 58q6-8 12 0" stroke="#c4a8ff" strokeWidth="4" fill="none" strokeLinecap="round" />
    <path d="M52 68q8 6 16 0" stroke="#c4a8ff" strokeWidth="3" fill="none" strokeLinecap="round" />
    <rect x="8" y="52" width="10" height="18" rx="5" fill="#8b5cf6" />
    <rect x="102" y="52" width="10" height="18" rx="5" fill="#8b5cf6" />
  </svg>
);

export default function OverviewPage() {
  return (
    <Suspense fallback={<div className="flex h-[400px] items-center justify-center">Loading…</div>}>
      <OverviewPageContent />
    </Suspense>
  );
}

function OverviewPageContent() {
  const { tasks, activity, toggleTask, settings, addTask } = useApp();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [cmd, setCmd] = useState(searchParams?.get("cmd") || "");
  const [modalTask, setModalTask] = useState<null | { id?: string }>(null);

  const active = tasks.filter(t => t.status !== "done");
  const done = tasks.length - active.length;
  const up = active.filter(t => t.due_date >= TODAY).sort((a, b) => a.due_date.localeCompare(b.due_date));
  const near = up.filter(t => t.due_date <= "2026-11-28").length;
  const run = (c: string) => router.push("/agent?cmd=" + encodeURIComponent(c));
  const kpi = [
    [ClipboardList, "Active Tasks", active.length, "+20%", 1],
    [CheckCircle2, "Completed Tasks", done, "+40%", 1],
    [CalendarClock, "Upcoming Deadlines", near, "-17%", 0],
    [Sparkles, "AI Actions", activity.length, "+50%", 1],
  ] as const;
  const mine = [...tasks].sort((a, b) => a.due_date.localeCompare(b.due_date)).slice(0, 4);
  const steps = activity.slice(0, 4);

  const handleOpenModal = (task?: { id?: string }) => setModalTask(task || {});
  const handleCloseModal = () => setModalTask(null);
  const handleSaveTask = (taskData: any) => {
    if (taskData.id) {
      // update
    } else {
      addTask(taskData);
    }
  };

  return (
    <AppShell>
      <div className="grid gap-5 xl:grid-cols-[1fr_320px]">
        <div className="min-w-0 space-y-5">
          <Card className="relative flex items-center justify-between overflow-hidden py-6">
            <div className="absolute inset-0 -z-10 bg-gradient-to-r from-brand-100/80 via-white/0 to-brand-200/70" />
            <div>
              <h1 className="text-3xl font-extrabold md:text-4xl">Hello, {settings?.name || "there"}! 👋</h1>
              <p className="mt-1 text-ink/65 md:text-lg">Ready to turn your plans into progress?</p>
            </div>
            <div className="hidden sm:block"><Robot /></div>
          </Card>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {kpi.map(([I, l, v, d, up], i) => (
              <Card key={l} className="hov p-4" style={{ animationDelay: i * 60 + "ms" }}>
                <div className="flex items-center gap-3">
                  <span className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-100 text-brand-600"><I size={22} /></span>
                  <div>
                    <div className="text-sm text-ink/70">{l}</div>
                    <div className="flex items-center gap-2">
                      <b className="text-3xl">{v}</b>
                      <Badge variant={up ? "low" : "high"}>{up ? "↑" : "↓"} {d.replace("-", "")}</Badge>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
          <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
            <Card>
              <Title right={<span className="chip bg-amber-100 text-amber-700">Demo Mode · simulated AI</span>}>
                Agent Command <Sparkles size={18} className="text-brand-500" />
              </Title>
              <p className="-mt-3 mb-3 text-sm text-ink/60">Tell SaarthiFlow what you want to do, and I'll plan the rest.</p>
              <div className="rounded-2xl border border-brand-100 bg-white/80 p-3">
                <Textarea
                  value={cmd}
                  onChange={e => setCmd(e.target.value)}
                  rows={2}
                  className="w-full resize-none bg-transparent text-sm outline-none"
                  placeholder="e.g. Analyze this hackathon page and create a task plan..."
                />
                <div className="flex items-center justify-between">
                  <Paperclip size={18} className="text-ink/40" />
                  <Button className="btn" onClick={() => run(cmd || "Analyze this hackathon page and create a task plan")}>
                    Run Agent <ArrowUpRight size={16} />
                  </Button>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  [Globe, "Analyze Webpage", "Analyze this webpage and extract deadlines"],
                  [CalendarDays, "Plan My Week", "Plan my week"],
                  [ListChecks, "Create Checklist", "Create a checklist for my hackathon submission"],
                ].map(([I, l, c]) => (
                  <Button key={l} variant="secondary" size="sm" className="!py-1.5" onClick={() => run(c)}>
                    <I size={16} />{l}
                  </Button>
                ))}
                <Button variant="secondary" size="sm" className="!py-1.5" onClick={() => router.push("/quick-actions")}>
                  <Plus size={16} />More
                </Button>
              </div>
            </Card>
            <Card className="relative overflow-hidden">
              <h3 className="text-xl font-extrabold leading-6">Use SaarthiFlow on Any Website</h3>
              <p className="mt-2 max-w-[180px] text-sm text-ink/65">Turn hackathons, internships and events into actionable tasks in one click.</p>
              <MousePointerClick className="absolute right-4 top-12 text-brand-400" size={64} />
              <Button className="btn mt-5" onClick={() => router.push("/extension")}>
                Get Extension <ArrowUpRight size={16} />
              </Button>
            </Card>
          </div>
          <div className="grid gap-5 lg:grid-cols-3">
            <Card>
              <Title icon={ClipboardList} right={<span className="text-sm font-semibold text-brand-600">View All →</span>}>
                My Tasks ({active.length})
              </Title>
              <div className="space-y-3">
                {mine.map(t => (
                  <div key={t.id} className="flex items-center gap-2 text-sm" onClick={() => handleOpenModal(t)}>
                    <CheckToggle checked={t.status === "done"} onChange={() => toggleTask(t.id)} />
                    <span className={`min-w-0 flex-1 truncate font-medium ${t.status === "done" ? "line-through text-ink/45" : ""}`}>
                      {t.title}
                    </span>
                    <Badge variant={t.priority.toLowerCase() as "high" | "medium" | "low"}>{t.priority}</Badge>
                    <span className="hidden text-xs text-ink/60 xl:block">{fmtD(t.due_date)}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card>
              <Title icon={BarChart3}>Weekly Productivity</Title>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weekly(tasks)}>
                    <XAxis dataKey="d" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={22} />
                    <Tooltip />
                    <Bar dataKey="n" name="Tasks due" fill="#b794f6" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card>
              <Title icon={CheckCircle2}>Action Insights</Title>
              <Donut data={groups(activity)} total={activity.length} />
            </Card>
          </div>
        </div>
        <div className="space-y-5">
          <Card>
            <Title icon={ActI}>Recent Agent Run</Title>
            <div className="space-y-4">
              {steps.map((a, i) => (
                <div key={a.id} className="flex gap-3">
                  <CheckCircle2 size={20} className={i === 0 ? "text-brand-600" : "text-brand-400"} />
                  <div className="min-w-0 flex-1">
                    <div className="flex justify-between text-sm font-semibold">
                      <span className="truncate">{a.title}</span>
                      <span className="ml-2 shrink-0 text-xs font-normal text-ink/50">{new Date(a.at).toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" })}</span>
                    </div>
                    <div className="truncate text-xs text-ink/55">{a.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <Title icon={CalendarDays}>Upcoming Deadlines</Title>
            <div className="space-y-3">
              {up.slice(0, 4).map(t => (
                <div key={t.id} className="flex items-center gap-2 text-sm">
                  <Trophy size={18} className="text-amber-500" />
                  <span className="flex-1 truncate font-medium">{t.title}</span>
                  <Badge variant="high">{fmtD(t.due_date)}</Badge>
                </div>
              ))}
              {!up.length && <Empty text="No upcoming deadlines." />}
            </div>
          </Card>
          <Card>
            <Title icon={BarChart3} right={<Badge variant="low">+50%</Badge>}>Activity Summary</Title>
            <div className="h-32">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={weekly(tasks).map(x => ({ ...x, n: x.n + 1 }))}>
                  <defs>
                    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0" stopColor="#a78bfa" stopOpacity=".5" />
                      <stop offset="1" stopColor="#a78bfa" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <Tooltip />
                  <Area dataKey="n" stroke="#7c3aed" fill="url(#g)" strokeWidth={2} type="monotone" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      </div>

      <TaskModal
        isOpen={!!modalTask}
        onClose={handleCloseModal}
        task={modalTask || undefined}
        onSave={handleSaveTask}
      />
    </AppShell>
  );
}

function Donut({ data, total }: { data: { name: string; value: number }[]; total: number }) {
  const d = data.length ? data : [{ name: "None", value: 1 }];
  return (
    <div>
      <div className="relative mx-auto h-36 w-36">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={d} dataKey="value" innerRadius={44} outerRadius={64} paddingAngle={2} stroke="none">
              {d.map((_, i) => <Cell key={i} fill={COL[i % 4]} />)}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 grid place-items-center text-center">
          <div>
            <b className="text-2xl">{total}</b>
            <div className="-mt-1 text-xs text-ink/60">Actions</div>
          </div>
        </div>
      </div>
      <div className="mt-2 space-y-1 text-xs">
        {data.map((x, i) => (
          <div key={x.name} className="flex items-center gap-2">
            <i className="h-2.5 w-2.5 rounded-full" style={{ background: COL[i % 4] }} />
            {x.name}<b className="ml-auto">{Math.round(x.value / total * 100)}%</b>
          </div>
        ))}
      </div>
    </div>
  );
}

function CheckToggle({ checked, onChange }: { checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`grid h-6 w-6 shrink-0 place-items-center rounded-md border-2 transition ${
        checked ? "border-brand-600 bg-brand-600 text-white" : "border-brand-200 bg-white hover:border-brand-500"
      }`}
    >
      {checked && <Check size={14} />}
    </button>
  );
}

// Need imports
import { Check, CheckCircle2 as CheckCircle2Icon } from "lucide-react";