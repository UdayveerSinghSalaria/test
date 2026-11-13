"use client";

import { useCallback, useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  CheckCircle2,
  Loader2,
  Mail,
  Plug,
  RefreshCw,
  ShieldAlert,
  Unplug,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiDelete, apiGet, ApiError } from "@/lib/api";
import type { Integration } from "@/types";

function GoogleGlyph() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" aria-hidden>
      <path fill="#4285F4" d="M23.5 12.3c0-.9-.1-1.5-.3-2.2H12v4.1h6.5c-.1 1.1-.8 2.7-2.4 3.8l3.7 2.9c2.3-2.1 3.7-5.1 3.7-8.6z" />
      <path fill="#34A853" d="M12 24c3.2 0 6-1.1 8-2.9l-3.8-2.9c-1 .7-2.4 1.2-4.2 1.2-3.2 0-6-2.1-6.9-5.1L1.2 17C3.2 21.1 7.3 24 12 24z" />
      <path fill="#FBBC05" d="M5.1 14.3c-.2-.7-.4-1.5-.4-2.3s.1-1.6.4-2.3L1.2 6.7C.4 8.3 0 10.1 0 12s.4 3.7 1.2 5.3l3.9-3z" />
      <path fill="#EA4335" d="M12 4.7c1.8 0 3 .8 3.7 1.4l3.3-3.2C17 1.2 14.8 0 12 0 7.3 0 3.2 2.9 1.2 6.7l3.9 3c.9-2.9 3.7-5 6.9-5z" />
    </svg>
  );
}

export default function IntegrationsPage() {
  return (
    <Suspense fallback={null}>
      <IntegrationsInner />
    </Suspense>
  );
}

function IntegrationsInner() {
  const router = useRouter();
  const params = useSearchParams();
  const [integration, setIntegration] = useState<Integration | null | undefined>(undefined);
  const [flash, setFlash] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [connectError, setConnectError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const row = await apiGet<Integration | null>(
        "/api/integrations/google/status"
      );
      setIntegration(row);
    } catch {
      setIntegration(null);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Status + flash messages returned by the OAuth callback redirect.
  useEffect(() => {
    const status = params.get("status");
    if (status === "connected") {
      setFlash({ kind: "ok", text: "Gmail connected successfully." });
      load();
      router.replace("/integrations");
    } else if (status === "error") {
      // Message arrives in an httpOnly flash cookie (read server-free via API? no—)
      // The backend sets `awa_flash`; we simply show a generic error and let
      // status endpoint tell the real state.
      setFlash({
        kind: "error",
        text: "Google sign-in did not complete. Check the backend logs and try again.",
      });
      router.replace("/integrations");
    }
  }, [params, router, load]);

  const connect = () => {
    setConnectError(null);
    // Full-page navigation: backend 302s to Google's official consent screen.
    window.location.href = "/api/integrations/google/connect";
  };

  const disconnect = async () => {
    setBusy(true);
    try {
      await apiDelete("/api/integrations/google");
      setIntegration(null);
      setFlash({ kind: "ok", text: "Gmail disconnected. Stored tokens were deleted." });
    } catch (err) {
      setFlash({
        kind: "error",
        text: err instanceof ApiError ? err.message : "Disconnect failed.",
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-6 md:px-6">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Integrations</h1>
          <p className="text-sm text-muted-foreground">
            Connect the external services the assistant can read from.
          </p>
        </div>

        {flash && (
          <div
            className={`rounded-md border px-3 py-2.5 text-sm ${
              flash.kind === "ok"
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                : "border-destructive/30 bg-destructive/10 text-destructive"
            }`}
          >
            {flash.text}
          </div>
        )}

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg border border-border">
                  <GoogleGlyph />
                </div>
                <div>
                  <CardTitle className="flex items-center gap-2 text-base">
                    Gmail
                    {integration && <Badge>Connected</Badge>}
                    {integration === null && (
                      <Badge variant="secondary">Not connected</Badge>
                    )}
                    {integration === undefined && (
                      <Badge variant="outline">Checking…</Badge>
                    )}
                  </CardTitle>
                  <CardDescription>
                    Read-only access to your inbox — latest emails, search, and
                    deadlines.
                  </CardDescription>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {integration ? (
              <>
                <div className="grid gap-2 rounded-md border border-border bg-muted/40 p-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Account</span>
                    <span className="flex items-center gap-1.5 font-medium">
                      <Mail className="size-3.5" />
                      {integration.provider_email || "(email hidden)"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Connected</span>
                    <span>
                      {new Date(integration.connected_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Access expires</span>
                    <span>
                      {integration.token_expiry
                        ? new Date(integration.token_expiry).toLocaleString()
                        : "n/a"}
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    <ShieldAlert className="mr-1 size-3" />
                    scopes: {integration.scopes.map((s) => s.split("/").pop()).join(", ")}
                  </Badge>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={load}>
                    <RefreshCw className="size-3.5" /> Refresh status
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={disconnect}
                    disabled={busy}
                  >
                    {busy ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <Unplug className="size-3.5" />
                    )}
                    Disconnect
                  </Button>
                </div>
              </>
            ) : integration === null ? (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Connect your Google account to let the assistant read your
                  inbox. You&apos;ll be sent to Google&apos;s official consent
                  screen; we never see or store your password.
                </p>
                {connectError && (
                  <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    {connectError}
                  </p>
                )}
                <Button onClick={connect}>
                  <Plug className="size-4" /> Connect Gmail
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" /> Checking connection…
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-dashed">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base text-muted-foreground">
              <CheckCircle2 className="size-4" /> Google Calendar
              <Badge variant="secondary">Coming soon</Badge>
            </CardTitle>
            <CardDescription>
              Calendar architecture is prepared but not implemented in this
              milestone — no fake connect button is shown on purpose.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    </AppShell>
  );
}
