"use client";

import React, { Suspense } from "react";
import { ClipboardList, CheckCircle2, CalendarClock, Sparkles, Paperclip, Globe, CalendarDays, ListChecks, Plus, ArrowUpRight, Trash2, Pencil, ChevronLeft, ChevronRight, Send, Check, X, Download, Search, Trophy, Activity as ActI, BarChart3, Bot, Circle, Loader2, Zap, Shield, MousePointerClick } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, AreaChart, Area } from "recharts";
import { useApp } from "@/context/app-context";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Title, Badge, Page } from "@/components/ui";

const COL = ["#7c3aed", "#b794f6", "#f472b6", "#e4d7ff"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const fmtD = (d: string) => { if (!d) return "No date"; const [, m, day] = d.split("-"); return MONTHS[+m - 1] + " " + +day; };
const dow = (d: string) => new Date(d + "T00:00:00").getDay();
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const weekly = (tasks: any[]) => [1, 2, 3, 4, 5, 6, 0].map(i => ({ d: DAYS[i], n: tasks.filter(t => dow(t.due_date) === i).length }));
const groups = (a: any[]) => { const c: Record<string, number> = {}; a.forEach(x => c[x.type] = (c[x.type] || 0) + 1); return Object.entries(c).map(([name, value]) => ({ name, value })); };

function AnalyticsPageContent() {
  const { tasks, activity } = useApp();
  const done = tasks.filter(t => t.status === "done").length;
  const rate = tasks.length ? Math.round(done / tasks.length * 100) : 0;
  const pri = ["High", "Medium", "Low"].map(p => ({ name: p, value: tasks.filter(t => t.priority === p).length }));
  const proj = [...new Set(tasks.map(t => t.project))].map(p => { const a = tasks.filter(t => t.project === p); return { name: p, pct: Math.round(a.filter(t => t.status === "done").length / a.length * 100) }; });

  return (
    <AppShell>
      <Page title="Analytics" sub="Live numbers from your tasks.">
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            ["Completion rate", rate + "%"],
            ["Total tasks", tasks.length],
            ["Logged actions", activity.length],
          ].map(([l, v]) => (
            <Card key={l} className="hov">
              <div className="text-sm text-ink/60">{l}</div>
              <b className="text-4xl">{v}</b>
            </Card>
          ))}
        </div>
        <div className="grid gap-5 lg:grid-cols-2">
          <Card>
            <Title icon={BarChart3}>Tasks due by weekday</Title>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weekly(tasks)}>
                  <CartesianGrid vertical={false} stroke="#ece3ff" />
                  <XAxis dataKey="d" />
                  <YAxis allowDecimals={false} width={24} />
                  <Tooltip />
                  <Bar dataKey="n" name="Tasks" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
          <Card>
            <Title>Priority distribution</Title>
            <Donut data={pri} total={tasks.length} />
          </Card>
          <Card className="lg:col-span-2">
            <Title>Project progress</Title>
            <div className="space-y-3">
              {proj.map(p => (
                <div key={p.name}>
                  <div className="flex justify-between text-sm"><b>{p.name}</b><span>{p.pct}%</span></div>
                  <div className="h-2.5 rounded-full bg-brand-100">
                    <div className="h-2.5 rounded-full bg-gradient-to-r from-brand-400 to-brand-600 transition-all" style={{ width: p.pct + "%" }} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </Page>
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
          <div><b className="text-2xl">{total}</b><div className="-mt-1 text-xs text-ink/60">Tasks</div></div>
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

export default function AnalyticsPage() {
  return (
    <Suspense fallback={<div className="flex h-[400px] items-center justify-center">Loading…</div>}>
      <AnalyticsPageContent />
    </Suspense>
  );
}