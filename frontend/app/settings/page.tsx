"use client";

import { useEffect, useState } from "react";
import { BadgeCheck, Bot, Loader2, Moon, Sun, User } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { apiGet } from "@/lib/api";
import { APP_NAME } from "@/lib/config";
import type { Health, Integration, User as UserType } from "@/types";

export default function SettingsPage() {
  const [user, setUser] = useState<UserType | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [integration, setIntegration] = useState<Integration | null | undefined>(undefined);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    Promise.allSettled([
      apiGet<UserType>("/api/auth/me"),
      apiGet<Health>("/api/health"),
      apiGet<Integration | null>("/api/integrations/google/status"),
    ]).then(([u, h, i]) => {
      if (u.status === "fulfilled") setUser(u.value);
      if (h.status === "fulfilled") setHealth(h.value);
      if (i.status === "fulfilled") setIntegration(i.value);
      setLoaded(true);
    });

    const stored = (localStorage.getItem("awa-theme") as "dark" | "light") || "dark";
    setTheme(stored);
  }, []);

  const switchTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("awa-theme", next);
    document.documentElement.classList.toggle("dark", next === "dark");
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-5 px-4 py-6 md:px-6">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
          <p className="text-sm text-muted-foreground">
            Account, appearance, and system configuration.
          </p>
        </div>

        {/* Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <User className="size-4" /> Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            {!loaded ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="size-4 animate-spin" /> Loading…
              </div>
            ) : user ? (
              <div className="grid gap-2">
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">Name</span>
                  <span className="font-medium">{user.name || "—"}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">Email</span>
                  <span className="font-medium">{user.email}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">Member since</span>
                  <span>{new Date(user.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">Session unavailable.</p>
            )}
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Appearance</CardTitle>
            <CardDescription>
              Dark-first theme with an optional light mode.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={switchTheme}>
              {theme === "dark" ? (
                <>
                  <Sun className="size-4" /> Switch to light
                </>
              ) : (
                <>
                  <Moon className="size-4" /> Switch to dark
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* System status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Bot className="size-4" /> System status
            </CardTitle>
            <CardDescription>
              Which capabilities are live in this deployment.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5 text-sm">
            <div className="flex items-center justify-between">
              <span>Application</span>
              <span className="font-medium">{health?.app_name ?? APP_NAME}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Gmail OAuth</span>
              <Badge variant={health?.google_oauth_configured ? "default" : "secondary"}>
                {health
                  ? health.google_oauth_configured
                    ? "Configured"
                    : "Missing client credentials"
                  : "…"}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span>Gmail connection</span>
              <Badge variant={integration ? "default" : "secondary"}>
                {integration === undefined
                  ? "…"
                  : integration
                    ? "Connected"
                    : "Not connected"}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span>AI provider (LLM)</span>
              <Badge variant={health?.llm_configured ? "default" : "secondary"}>
                {health
                  ? health.llm_configured
                    ? "Configured"
                    : "Not configured (agent disabled)"
                  : "…"}
              </Badge>
            </div>
            <p className="flex items-start gap-1.5 pt-2 text-xs text-muted-foreground">
              <BadgeCheck className="mt-0.5 size-3.5 shrink-0" />
              Secrets (Google client secret, encryption key, session secret,
              LLM key) live only in backend environment variables.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
