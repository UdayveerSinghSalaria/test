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
  Trash2,
  Pencil,
  ChevronLeft,
  ChevronRight,
  Send,
  Check,
  X,
  Download,
  Search,
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
import { useApp } from "@/context/app-context";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Title, Badge, Page, Empty, TaskModal } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const STAGES = ["Understand", "Plan", "Approve", "Execute", "Verify"];

function makePlan(c: string) {
  const l = c.toLowerCase();
  const mk = (title: string, priority: "High" | "Medium" | "Low", due: string, project: string) => ({ id: crypto.randomUUID(), title, priority, due, project });
  if (l.includes("week")) return [mk("Review all pending deadlines", "High", "2026-11-15", "Planning"), mk("Block 2h deep-work for MVP", "High", "2026-11-16", "Hackathon"), mk("Weekly retro and next-week plan", "Low", "2026-11-21", "Planning")];
  if (l.includes("checklist")) return [mk("Finalize README and screenshots", "Medium", "2026-11-18", "Hackathon"), mk("Record 2-minute demo video", "High", "2026-11-19", "Hackathon"), mk("Submit project on portal", "High", "2026-11-20", "Hackathon")];
  if (l.includes("overdue") || l.includes("reschedule")) return [mk("Reschedule overdue tasks to this week", "Medium", "2026-11-16", "Planning"), mk("Clear one blocked task today", "High", "2026-11-15", "Planning")];
  return [mk("Register for the event", "High", "2026-11-17", "Hackathon"), mk("Note eligibility and requirements", "Medium", "2026-11-18", "Hackathon"), mk("Draft idea and team roles", "Medium", "2026-11-21", "Hackathon"), mk("Submit final entry before deadline", "High", "2026-11-28", "Hackathon")];
}

function AgentPageContent() {
  const { addProposal } = useApp();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [cmd, setCmd] = useState(searchParams.get("cmd") || "");
  const [msgs, setMsgs] = useState<Array<{ r: "ai" | "me"; t: string }>>([
    { r: "ai", t: "Hi! Give me a goal and I'll draft a task plan for your approval. (Demo Mode: plans are simulated locally.)" }
  ]);
  const [plan, setPlan] = useState<{ title: string; tasks: Array<{ id: string; title: string; project: string; priority: "High" | "Medium" | "Low"; due: string }> } | null>(null);
  const [st, setSt] = useState(0);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [modalTask, setModalTask] = useState<null | { id?: string }>(null);

  React.useEffect(() => { setCmd(searchParams.get("cmd") || "") }, [searchParams]);

  const gen = () => {
    if (!cmd.trim() || busy) return;
    const c = cmd;
    setBusy(true);
    setSent(false);
    setSt(0);
    setMsgs(m => [...m, { r: "me", t: c }]);
    setCmd("");
    setTimeout(() => {
      setSt(1);
      const p = makePlan(c);
      setPlan({ title: c, tasks: p });
      setMsgs(m => [...m, { r: "ai", t: `I drafted ${p.length} tasks. Edit them below, then send for approval.` }]);
      setBusy(false);
    }, 900);
  };

  const ed = (id: string, k: string, v: string) => setPlan(p => ({ ...p!, tasks: p!.tasks.map(t => t.id === id ? { ...t, [k]: v } : t) }));
  const send = () => {
    addProposal({ title: plan!.title, source: "Agent Studio", tasks: plan!.tasks });
    setSt(2);
    setSent(true);
    setMsgs(m => [...m, { r: "ai", t: "Plan sent. Open Approvals to approve or reject it." }]);
  };

  const handleOpenModal = (task?: { id?: string }) => setModalTask(task || {});
  const handleCloseModal = () => setModalTask(null);
  const handleSaveTask = (taskData: any) => {
    if (plan) {
      setPlan(p => ({ ...p!, tasks: taskData.id ? p!.tasks.map(t => t.id === taskData.id ? { ...taskData, id: taskData.id } : t) : [...p!.tasks, { ...taskData, id: crypto.randomUUID() }] }));
    }
    handleCloseModal();
  };

  return (
    <AppShell>
      <Page title="Agent Studio" sub="Describe a goal and review the plan before anything happens." right={<Badge variant="medium">Demo Mode · simulated AI</Badge>}>
        <Card className="p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            {STAGES.map((s, i) => (
              <div key={s} className={`flex items-center gap-2 text-sm font-semibold ${i <= st ? "text-brand-700" : "text-ink/40"}`}>
                <span className={`grid h-7 w-7 place-items-center rounded-full text-xs ${i <= st ? "bg-brand-600 text-white" : "bg-brand-50"}`}>
                  {i < st ? <Check size={14} /> : i + 1}
                </span>
                {s}
              </div>
            ))}
          </div>
        </Card>
        <div className="grid gap-5 lg:grid-cols-2">
          <Card className="flex min-h-[420px] flex-col">
            <div className="flex-1 space-y-3 overflow-y-auto">
              {msgs.map((m, i) => (
                <div key={i} className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${m.r === "me" ? "ml-auto bg-brand-600 text-white" : "bg-white/90"}`}>
                  {m.t}
                </div>
              ))}
              {busy && <div className="flex items-center gap-2 text-sm text-ink/60"><Loader2 className="animate-spin" size={16} />Planning…</div>}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {["Analyze this hackathon page", "Plan my week", "Create a checklist for submission"].map(s => (
                <Button key={s} variant="secondary" size="sm" className="!px-3 !py-1 !text-xs" onClick={() => setCmd(s)}>{s}</Button>
              ))}
            </div>
            <div className="mt-3 flex gap-2">
              <Input value={cmd} onChange={e => setCmd(e.target.value)} onKeyDown={e => e.key === "Enter" && gen()} placeholder="Tell the agent what to do…" />
              <Button onClick={gen} disabled={busy}><Sparkles size={16} />Generate Plan</Button>
            </div>
          </Card>
          <Card>
            <Title icon={ListChecks}>Proposed tasks</Title>
            {!plan ? <Empty text="Generate a plan to see editable tasks here." /> : (
              <div className="space-y-3">
                {plan.tasks.map(t => (
                  <div key={t.id} className="space-y-2 rounded-2xl bg-white/70 p-3" onClick={() => handleOpenModal(t)}>
                    <Input className="font-semibold" value={t.title} onChange={e => ed(t.id, "title", e.target.value)} />
                    <div className="flex gap-2">
                      <Select value={t.priority} onChange={e => ed(t.id, "priority", e.target.value)} options={["High", "Medium", "Low"].map(x => ({ value: x, label: x }))} />
                      <Input type="date" value={t.due} onChange={e => ed(t.id, "due", e.target.value)} />
                      <Button variant="ghost" size="sm" aria-label="Remove" onClick={() => setPlan(p => ({ ...p!, tasks: p!.tasks.filter(x => x.id !== t.id) }))}>
                        <Trash2 size={16} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
        <Card>
          {sent ? (
            <Button className="w-full" onClick={() => router.push("/approvals")}><Send size={16} />Go to Approvals <ArrowUpRight size={16} /></Button>
          ) : (
            <Button className="w-full" disabled={!plan?.tasks.length} onClick={send}><Send size={16} />Send for Approval</Button>
          )}
        </Card>
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

export default function AgentPage() {
  return (
    <Suspense fallback={<div className="flex h-[400px] items-center justify-center">Loading…</div>}>
      <AgentPageContent />
    </Suspense>
  );
}