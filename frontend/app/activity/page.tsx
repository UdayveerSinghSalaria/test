"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Ban,
  History,
  Info,
  Loader2,
  ListChecks,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { apiGet } from "@/lib/api";
import type { Activity } from "@/types";

const KIND_META: Record<Activity["kind"], { icon: React.ElementType; label: string }> = {
  tool_call: { icon: ListChecks, label: "Tool" },
  plan: { icon: Info, label: "Plan" },
  approval: { icon: ShieldCheck, label: "Approval" },
  error: { icon: Ban, label: "Error" },
  info: { icon: Info, label: "Info" },
};

export default function ActivityPage() {
  const [items, setItems] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const rows = await apiGet<Activity[]>("/api/activity?limit=100");
      setItems(rows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load activity.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-5 px-4 py-6 md:px-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Activity History
            </h1>
            <p className="text-sm text-muted-foreground">
              Full audit trail of the assistant&apos;s actions. Email contents
              are never logged.
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={load}>
            <RefreshCw className="size-3.5" /> Refresh
          </Button>
        </div>

        {error && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        {loading ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-12 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
              <History className="size-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                No activity recorded yet. Run the assistant to see it work.
              </p>
              <Loader2 className="hidden" />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <ul>
                {items.map((a) => {
                  const meta = KIND_META[a.kind] ?? KIND_META.info;
                  const Icon = meta.icon;
                  return (
                    <li
                      key={a.id}
                      className="flex items-center gap-3 border-b border-border px-4 py-3 last:border-b-0"
                    >
                      <Icon
                        className={`size-4 shrink-0 ${
                          a.status === "error" || a.kind === "error"
                            ? "text-destructive"
                            : a.kind === "approval"
                              ? "text-amber-500"
                              : "text-muted-foreground"
                        }`}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-medium">{a.action}</span>
                          <Badge variant="outline" className="text-[10px]">
                            {meta.label}
                          </Badge>
                          {a.status !== "ok" && (
                            <Badge
                              variant={a.status === "error" ? "destructive" : "secondary"}
                              className="text-[10px]"
                            >
                              {a.status}
                            </Badge>
                          )}
                        </div>
                        {a.detail && (
                          <p className="mt-0.5 truncate text-xs text-muted-foreground">
                            {a.detail}
                          </p>
                        )}
                      </div>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {new Date(a.created_at).toLocaleString()}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
