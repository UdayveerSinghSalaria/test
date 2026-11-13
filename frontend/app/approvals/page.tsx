"use client";

import React, { useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { ClipboardList, CheckCircle2, CalendarClock, Sparkles, Paperclip, Globe, CalendarDays, ListChecks, Plus, ArrowUpRight, Trash2, Pencil, ChevronLeft, ChevronRight, Send, Check, X, Download, Search, Trophy, Activity as ActI, BarChart3, Bot, Circle, Loader2, Zap, Shield, MousePointerClick } from "lucide-react";
import { useApp } from "@/context/app-context";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Title, Badge, Page, Empty, TaskModal } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const tm = (t: number) => new Date(t).toLocaleString("en-IN", { hour: "numeric", minute: "2-digit", day: "numeric", month: "short" });

function ApprovalsPageContent() {
  const { proposals, decideProposal } = useApp();
  const router = useRouter();
  const [tab, setTab] = useState("pending");
  const [ed, setEd] = useState<Record<string, any[]>>({});

  const list = proposals.filter(p => p.status === tab);
  const tasksOf = (p: any) => ed[p.id] || p.tasks;
  const chg = (p: any, id: string, k: string, v: string) => setEd({ ...ed, [p.id]: tasksOf(p).map(t => t.id === id ? { ...t, [k]: v } : t) });

  return (
    <AppShell>
      <Page title="Approvals" sub="Nothing is created until you approve it.">
        <div className="glass rounded-xl inline-flex p-1">
          {["pending", "approved", "rejected"].map(t => (
            <Button key={t} variant={tab === t ? "primary" : "secondary"} size="sm" onClick={() => setTab(t)} className="capitalize">
              {t.charAt(0).toUpperCase() + t.slice(1)} ({proposals.filter(p => p.status === t).length})
            </Button>
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {list.map(p => (
            <Card key={p.id}>
              <div className="mb-3 flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-bold">{p.title}</h3>
                  <p className="text-xs text-ink/55">{p.source} · {tm(p.created)}</p>
                </div>
                <Badge variant={p.status === "pending" ? "medium" : p.status === "approved" ? "low" : "high"}>{p.status.charAt(0).toUpperCase() + p.status.slice(1)}</Badge>
              </div>
              <div className="space-y-2">
                {tasksOf(p).map(t => p.status === "pending" ? (
                  <div key={t.id} className="flex flex-wrap gap-2">
                    <Input value={t.title} onChange={e => chg(p, t.id, "title", e.target.value)} />
                    <Input type="date" value={t.due} onChange={e => chg(p, t.id, "due", e.target.value)} className="inp w-auto" />
                  </div>
                ) : (
                  <div key={t.id} className="flex items-center gap-2 text-sm">
                    <Badge variant={t.priority.toLowerCase() as "high" | "medium" | "low"}>{t.priority}</Badge>
                    {t.title}
                    <span className="ml-auto text-xs text-ink/55">{fmtD(t.due)}</span>
                  </div>
                ))}
              </div>
              {p.status === "pending" && (
                <div className="mt-4 flex gap-2">
                  <Button className="flex-1" onClick={() => decideProposal(p.id, { approved: true, tasks: tasksOf(p) })}><Check size={16} />Approve</Button>
                  <Button variant="secondary" className="flex-1 text-rose-600" onClick={() => decideProposal(p.id, { approved: false })}><X size={16} />Reject</Button>
                </div>
              )}
            </Card>
          ))}
        </div>
        {!list.length && <Empty text={`No ${tab} proposals. Generate a plan in Agent Studio.`} />}
      </Page>
    </AppShell>
  );
}

function fmtD(d: string) {
  if (!d) return "No date";
  const [, m, day] = d.split("-");
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return MONTHS[+m - 1] + " " + +day;
}

export default function ApprovalsPage() {
  return (
    <Suspense fallback={<div className="flex h-[400px] items-center justify-center">Loading…</div>}>
      <ApprovalsPageContent />
    </Suspense>
  );
}