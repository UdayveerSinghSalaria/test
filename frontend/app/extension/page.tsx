"use client";

import React, { Suspense } from "react";
import { Globe, Shield, Zap, Monitor, Download } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, Title, Page, Badge } from "@/components/ui";
import { Button } from "@/components/ui/button";

function ExtensionPageContent() {
  return (
    <AppShell>
      <Page title="Get Extension" sub="Turn any webpage into an action plan." right={<Button disabled className="cursor-not-allowed opacity-70"><Download size={16} />Coming Soon</Button>}>
        <div className="grid gap-4 md:grid-cols-3">
          {[
            [Globe, "Reads the page you're on", "Pulls deadlines, requirements and links from hackathon and internship pages."],
            [Shield, "You stay in control", "Every plan waits for your approval before tasks are created."],
            [Zap, "One-click to tasks", "Send the plan straight to My Space."],
          ].map(([I, t, d]) => (
            <Card key={t} className="hov">
              <I className="text-brand-600" size={28} />
              <h3 className="mt-3 font-bold">{t}</h3>
              <p className="text-sm text-ink/60">{d}</p>
            </Card>
          ))}
        </div>
        <Card>
          <Title icon={Monitor}>How installation will work</Title>
          <ol className="space-y-3">
            {[
              "Download the extension package when it is released.",
              "Open chrome://extensions and enable Developer mode.",
              "Choose Load unpacked and select the folder.",
              "Pin SaarthiFlow and click it on any webpage.",
            ].map((s, i) => (
              <li key={i} className="flex items-center gap-3 text-sm">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-brand-600 text-xs font-bold text-white">{i + 1}</span>
                {s}
              </li>
            ))}
          </ol>
          <p className="mt-4 text-xs text-ink/50">The extension is not built yet. This page is a preview.</p>
        </Card>
      </Page>
    </AppShell>
  );
}

export default function ExtensionPage() {
  return (
    <Suspense fallback={<div className="flex h-[400px] items-center justify-center">Loading…</div>}>
      <ExtensionPageContent />
    </Suspense>
  );
}