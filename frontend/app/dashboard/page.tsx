"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  Circle,
  Clock,
  Inbox as InboxIcon,
  ListTodo,
  Loader2,
  Plug,
  ShieldCheck,
  Sparkles,
  History,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { apiGet } from "@/lib/api";
import { APP_NAME } from "@/lib/config";
import type { Activity, EmailListResponse, Health, Integration, Task, User } from "@/types";

function StatCard({
  title,
  value,
  icon: Icon,
  hint,
  loading,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  hint?: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">{title}</span>
          <Icon className="size-4 text-muted-foreground" />
        </div>
        <div className="mt-2 text-2xl font-semibold tracking-tight">
          {loading ? "—" : value}
        </div>
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [integration, setIntegration] = useState<Integration | null | undefined>(undefined);
  const [emails, setEmails] = useState<EmailListResponse | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [quick, setQuick] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const results = await Promise.allSettled([
      apiGet<User>("/api/auth/me"),
      apiGet<Task[]>("/api/tasks"),
      apiGet<Activity[]>("/api/activity?limit=6"),
      apiGet<Integration | null>("/api/integrations/google/status"),
      apiGet<EmailListResponse>("/api/emails?limit=3"),
      apiGet<Health>("/api/health"),
    ]);
    const [u, t, a, i, e, h] = results;
    if (u.status === "fulfilled") setUser(u.value);
    if (t.status === "fulfilled") setTasks(t.value);
    if (a.status === "fulfilled") setActivity(a.value);
    if (i.status === "fulfilled") setIntegration(i.value);
    if (e.status === "fulfilled") setEmails(e.value);
    if (h.status === "fulfilled") setHealth(h.value);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const pending = useMemo(
    () => tasks.filter((t) => t.status !== "completed"),
    [tasks]
  );
  const completed = useMemo(
    () => tasks.filter((t) => t.status === "completed"),
    [tasks]
  );
  const upcoming = useMemo(
    () =>
      pending
        .filter((t) => t.due_date)
        .sort((a, b) => (a.due_date! < b.due_date! ? -1 : 1))
        .slice(0, 4),
    [pending]
  );

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 18) return "Good afternoon";
    return "Good evening";
  })();

  const submitQuick = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = quick.trim();
    if (!q) return;
    setQuick("");
    // Hand the instruction to the assistant page, which runs the real agent.
    router.push(`/assistant?q=${encodeURIComponent(q)}`);
  };

  const connectionLabel = integration
    ? "Gmail connected"
    : integration === null
      ? "Gmail not connected"
      : "Checking…";

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-6 md:px-6">
        {/* Greeting + quick action */}
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            {greeting}
            {user ? `, ${user.name || user.email.split("@")[0]}` : ""}
          </h1>
          <p className="text-sm text-muted-foreground">
            Here&apos;s what&apos;s happening in your workspace.
          </p>
        </div>

        <form onSubmit={submitQuick} className="flex gap-2">
          <Input
            value={quick}
            onChange={(e) => setQuick(e.target.value)}
            placeholder="Ask the assistant… e.g. “find deadlines in my inbox this week”"
            className="flex-1"
          />
          <Button type="submit" disabled={!quick.trim()}>
            <Sparkles className="size-4" />
            Run
          </Button>
        </form>

        {/* Stats */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Pending tasks"
            value={pending.length}
            icon={ListTodo}
            loading={loading}
            hint={pending.length ? undefined : "No open tasks"}
          />
          <StatCard
            title="Completed"
            value={completed.length}
            icon={CheckCircle2}
            loading={loading}
          />
          <StatCard
            title="Upcoming deadlines"
            value={upcoming.length}
            icon={Clock}
            loading={loading}
            hint={upcoming[0] ? `Next: ${new Date(upcoming[0].due_date!).toLocaleDateString()}` : "Nothing due"}
          />
          <StatCard
            title="Inbox"
            value={emails ? emails.emails.length : "—"}
            icon={InboxIcon}
            loading={loading}
            hint={
              integration
                ? `${emails?.emails.length ?? 0} latest shown`
                : "Connect Gmail to see it"
            }
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          {/* Recent activity */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Recent agent activity</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => router.push("/activity")}>
                  View all <ArrowRight className="size-3.5" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-2">
                  {[0, 1, 2].map((i) => (
                    <div key={i} className="h-9 animate-pulse rounded bg-muted" />
                  ))}
                </div>
              ) : activity.length === 0 ? (
                <div className="flex flex-col items-center gap-2 py-8 text-center">
                  <History className="size-8 text-muted-foreground/50" />
                  <p className="text-sm text-muted-foreground">
                    No agent activity yet. Ask the assistant something.
                  </p>
                </div>
              ) : (
                <ul className="space-y-1">
                  {activity.map((a) => (
                    <li
                      key={a.id}
                      className="flex items-center gap-3 rounded-md px-2 py-1.5 text-sm hover:bg-accent/50"
                    >
                      <Badge
                        variant="outline"
                        className="shrink-0 text-[10px] uppercase"
                      >
                        {a.kind.replace("_", " ")}
                      </Badge>
                      <span className="font-medium">{a.action}</span>
                      <span className="min-w-0 flex-1 truncate text-muted-foreground">
                        {a.detail}
                      </span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {new Date(a.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          {/* Side column */}
          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Upcoming deadlines</CardTitle>
              </CardHeader>
              <CardContent>
                {upcoming.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nothing due soon.</p>
                ) : (
                  <ul className="space-y-2">
                    {upcoming.map((t) => (
                      <li key={t.id} className="flex items-center gap-2 text-sm">
                        <Circle className="size-3 text-muted-foreground" />
                        <span className="min-w-0 flex-1 truncate">{t.title}</span>
                        <span className="shrink-0 text-xs text-muted-foreground">
                          {new Date(t.due_date!).toLocaleDateString([], {
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Integrations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <InboxIcon className="size-4 text-muted-foreground" /> Gmail
                  </span>
                  <Badge variant={integration ? "default" : "secondary"}>
                    {connectionLabel}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <ShieldCheck className="size-4 text-muted-foreground" /> Agent
                  </span>
                  <Badge variant={health?.llm_configured ? "default" : "secondary"}>
                    {health === null ? "…" : health.llm_configured ? "Configured" : "Needs API key"}
                  </Badge>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => router.push("/integrations")}
                >
                  <Plug className="size-3.5" /> Manage
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        <p className="pt-2 text-center text-xs text-muted-foreground">
          {APP_NAME} — Gmail is live; Calendar and autonomous execution are not
          wired up yet and are labeled where they appear.
        </p>
      </div>
    </AppShell>
  );
}
