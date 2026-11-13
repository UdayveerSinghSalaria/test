"use client";

import React, { Suspense } from "react";
import { useRouter } from "next/navigation";
import { Globe, CalendarDays, ListChecks, CalendarClock } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Title, Page, Badge } from "@/components/ui";
import { Button } from "@/components/ui/button";

const A = [
  [Globe, "Analyze Webpage", "Analyze this webpage and extract deadlines and requirements"],
  [CalendarDays, "Plan My Week", "Plan my week"],
  [ListChecks, "Create Checklist", "Create a checklist for my hackathon submission"],
  [CalendarClock, "Reschedule Overdue Tasks", "Reschedule overdue tasks"],
];

export default function QuickActionsPage() {
  return (
    <Suspense fallback={<div className="flex h-[400px] items-center justify-center">Loading…</div>}>
      <QuickActionsPageContent />
    </Suspense>
  );
}

function QuickActionsPageContent() {
  const router = useRouter();

  return (
    <AppShell>
      <Page title="Quick Actions" sub="One click opens Agent Studio with the command ready.">
        <div className="grid gap-4 sm:grid-cols-2">
          {A.map(([I, l, c]) => (
            <Button key={l} onClick={() => router.push("/agent?cmd=" + encodeURIComponent(c))} className="text-left">
              <Card className="hov h-full">
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-brand-100 text-brand-600"><I size={24} /></span>
                <h3 className="mt-3 text-lg font-bold">{l}</h3>
                <p className="text-sm text-ink/60">"{c}"</p>
              </Card>
            </Button>
          ))}
        </div>
      </Page>
    </AppShell>
  );
}