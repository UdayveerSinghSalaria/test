"use client";

import React, { useState, useEffect, Suspense } from "react";
import { ClipboardList, CheckCircle2, CalendarClock, Sparkles, Paperclip, Globe, CalendarDays, ListChecks, Plus, ArrowUpRight, Trash2, Pencil, ChevronLeft, ChevronRight, Send, Check, X, Download, Chrome, Search, Trophy, Activity as ActI, BarChart3, Bot, Circle, Loader2, Zap, Shield, MousePointerClick, RefreshCw, Bot as BotIcon } from "lucide-react";
import { useApp } from "@/context/app-context";
import { useAuth } from "@/context/auth-context";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Title, Badge, Page } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { apiGet } from "@/lib/api";

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="flex h-[400px] items-center justify-center">Loading…</div>}>
      <SettingsPageContent />
    </Suspense>
  );
}

function SettingsPageContent() {
  const { settings, saveSettings, reset } = useApp();
  const { user, logout } = useAuth();
  const [v, setV] = useState(settings || { name: "", email: "", role: "", weekStart: "Mon", notify: true });
  const [ok, setOk] = useState(false);
  const [apStatus, setApStatus] = useState<{ provider_email?: string; scopes?: string[] } | null>(null);
  const [apLoading, setApLoading] = useState(true);

  useEffect(() => {
    apiGet<{ provider_email?: string; scopes?: string[] } | null>("/api/integrations/activepieces/status")
      .then(setApStatus)
      .catch(() => setApStatus(null))
      .finally(() => setApLoading(false));
  }, []);

  const u = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setV({ ...v, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  const handleSave = async () => {
    await saveSettings(v);
    setOk(true);
    setTimeout(() => setOk(false), 1800);
  };

  const handleLogout = async () => {
    await logout();
  };

  return (
    <AppShell>
      <Page title="Settings" sub="Stored only in this browser.">
        <Card className="max-w-xl space-y-4">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-brand-50 border border-brand-200">
            <div className="grid h-12 w-12 place-items-center rounded-xl bg-brand-600 text-white">
              {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
            </div>
            <div>
              <p className="font-semibold">{v.name || user?.name || "User"}</p>
              <p className="text-sm text-ink/60">{v.email || user?.email}</p>
            </div>
          </div>

          {[["name", "Name"], ["email", "Email"], ["role", "Role"]].map(([k, l]) => (
            <label key={k} className="block text-sm font-semibold">
              {l}
              <Input className="mt-1" value={v[k] || ""} onChange={u(k)} />
            </label>
          ))}

          <label className="block text-sm font-semibold">
            Week starts on
            <Select className="mt-1" value={v.weekStart || "Mon"} onChange={u("weekStart")} options={[{ value: "Mon", label: "Mon" }, { value: "Sun", label: "Sun" }]} />
          </label>

          <label className="flex items-center gap-2 text-sm font-semibold">
            <input type="checkbox" checked={v.notify} onChange={u("notify")} className="rounded border-brand-200 text-brand-600 focus:ring-brand-500" />
            Show approval reminders
          </label>

          <div className="flex flex-wrap gap-2">
            <Button onClick={handleSave} disabled={ok}>
              {ok ? <RefreshCw className="size-4 animate-spin" /> : <>Save changes</>}
            </Button>
            <Button variant="secondary" onClick={() => confirm("Reset all demo data?") && reset()}>Reset demo data</Button>
            <Button variant="secondary" className="!text-rose-600" onClick={handleLogout}>Logout</Button>
            {ok && <span className="self-center text-sm font-semibold text-emerald-600">Saved</span>}
          </div>

          <div className="pt-4 border-t border-brand-100">
            <h4 className="font-semibold mb-2">Integrations</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between rounded-xl border border-brand-200 bg-white/80 p-3">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-brand-100 text-brand-600"><BotIcon size={20} /></div>
                  <div>
                    <p className="font-medium">Gmail (Google OAuth)</p>
                    <p className="text-xs text-ink/50">Read-only access to your inbox</p>
                  </div>
                </div>
                <Badge variant="secondary">Not connected</Badge>
              </div>
              <div className="flex items-center justify-between rounded-xl border border-brand-200 bg-white/80 p-3">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-amber-100 text-amber-600"><Zap size={20} /></div>
                  <div>
                    <p className="font-medium">Activepieces (Shared)</p>
                    <p className="text-xs text-ink/50">{apStatus?.provider_email || "relan.toshan@gmail.com · gmail.readonly"}</p>
                  </div>
                </div>
                {apLoading ? (
                  <Badge variant="outline">Checking…</Badge>
                ) : apStatus ? (
                  <Badge variant="default">Connected</Badge>
                ) : (
                  <Badge variant="destructive">Not configured</Badge>
                )}
              </div>
            </div>
          </div>
        </Card>
      </Page>
    </AppShell>
  );
}

async function handleSave() {}
async function handleLogout() {}