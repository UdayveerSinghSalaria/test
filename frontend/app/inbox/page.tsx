"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Inbox as InboxIcon,
  Loader2,
  Mail,
  Paperclip,
  Plug,
  Search,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiGet, ApiError } from "@/lib/api";
import type { EmailDetail, EmailListResponse, EmailSummary } from "@/types";

function formatDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  if (sameDay) return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (d.getFullYear() === now.getFullYear())
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
  return d.toLocaleDateString([], { year: "numeric", month: "short", day: "numeric" });
}

function EmailRow({
  email,
  active,
  onClick,
}: {
  email: EmailSummary;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full border-b border-border px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-accent/50 ${
        active ? "bg-accent" : ""
      }`}
    >
      <div className="flex items-baseline justify-between gap-3">
        <span
          className={`min-w-0 truncate text-sm ${
            email.is_unread ? "font-semibold text-foreground" : "text-foreground/90"
          }`}
        >
          {email.sender_name || email.sender_email || "(unknown sender)"}
        </span>
        <span className="shrink-0 text-xs text-muted-foreground">
          {formatDate(email.received_at)}
        </span>
      </div>
      <div className="mt-0.5 flex items-center gap-2">
        {email.is_unread && (
          <span className="size-1.5 shrink-0 rounded-full bg-primary" />
        )}
        <span className="min-w-0 truncate text-sm text-muted-foreground">
          {email.subject}
        </span>
      </div>
      <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground/80">
        {email.snippet}
      </p>
    </button>
  );
}

export default function InboxPage() {
  const router = useRouter();
  const [emails, setEmails] = useState<EmailSummary[]>([]);
  const [nextToken, setNextToken] = useState<string | null>(null);
  const [selected, setSelected] = useState<EmailDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notConnected, setNotConnected] = useState(false);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);

  const fetchEmails = useCallback(
    async (opts: { q?: string; pageToken?: string; append: boolean }) => {
      setError(null);
      const params = new URLSearchParams({ limit: "5" });
      if (opts.q) params.set("q", opts.q);
      if (opts.pageToken) params.set("page_token", opts.pageToken);
      try {
        const res = await apiGet<EmailListResponse>(`/api/emails?${params}`);
        setEmails((prev) =>
          opts.append ? [...prev, ...res.emails] : res.emails
        );
        setNextToken(res.next_page_token);
        setNotConnected(false);
      } catch (err) {
        if (err instanceof ApiError && err.status === 409) {
          setNotConnected(true);
        } else {
          setError(err instanceof Error ? err.message : "Failed to load emails.");
        }
        if (!opts.append) setEmails([]);
        setNextToken(null);
      } finally {
        setLoading(false);
        setLoadingMore(false);
        setSearching(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchEmails({ append: false });
  }, [fetchEmails]);

  const search = async (e: React.FormEvent) => {
    e.preventDefault();
    setSearching(true);
    setSelected(null);
    await fetchEmails({ q: query.trim() || undefined, append: false });
  };

  const clearSearch = async () => {
    setQuery("");
    setSelected(null);
    await fetchEmails({ append: false });
  };

  const openEmail = async (id: string) => {
    setDetailLoading(true);
    setError(null);
    try {
      const detail = await apiGet<EmailDetail>(`/api/emails/${id}`);
      setSelected(detail);
      // Optimistic unread -> read in the list view
      setEmails((prev) =>
        prev.map((e) => (e.id === id ? { ...e, is_unread: false } : e))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open email.");
    } finally {
      setDetailLoading(false);
    }
  };

  const loadMore = () => {
    if (!nextToken) return;
    setLoadingMore(true);
    fetchEmails({ q: query.trim() || undefined, pageToken: nextToken, append: true });
  };

  return (
    <AppShell>
      <div className="flex h-full flex-col px-4 py-6 md:px-6">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Inbox</h1>
            <p className="text-sm text-muted-foreground">
              Live from your connected Gmail account.
            </p>
          </div>
          <form onSubmit={search} className="flex w-full max-w-sm gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search mail (from:, subject:, is:unread…)"
                className="pl-8"
              />
            </div>
            <Button type="submit" variant="secondary" disabled={searching}>
              {searching ? <Loader2 className="size-4 animate-spin" /> : "Search"}
            </Button>
            {query && (
              <Button type="button" variant="ghost" onClick={clearSearch}>
                Clear
              </Button>
            )}
          </form>
        </div>

        {notConnected ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
              <Plug className="size-8 text-muted-foreground/60" />
              <p className="text-sm text-muted-foreground">
                Gmail isn&apos;t connected yet. Connect your Google account to
                see real emails here.
              </p>
              <Button onClick={() => router.push("/integrations")}>
                Go to Integrations
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-2">
            {/* List */}
            <Card className="flex min-h-[420px] flex-col overflow-hidden">
              <CardContent className="flex-1 overflow-y-auto p-0">
                {loading ? (
                  <div className="space-y-3 p-4">
                    {[0, 1, 2, 3, 4].map((i) => (
                      <div key={i} className="space-y-1.5">
                        <div className="h-3.5 w-1/3 animate-pulse rounded bg-muted" />
                        <div className="h-3 w-2/3 animate-pulse rounded bg-muted" />
                      </div>
                    ))}
                  </div>
                ) : error && emails.length === 0 ? (
                  <div className="flex flex-col items-center gap-2 py-12 text-center">
                    <Mail className="size-8 text-destructive/70" />
                    <p className="text-sm text-muted-foreground">{error}</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchEmails({ q: query || undefined, append: false })}
                    >
                      Retry
                    </Button>
                  </div>
                ) : emails.length === 0 ? (
                  <div className="flex flex-col items-center gap-2 py-12 text-center">
                    <InboxIcon className="size-8 text-muted-foreground/50" />
                    <p className="text-sm text-muted-foreground">
                      {query
                        ? `No emails match “${query}”.`
                        : "Your inbox is empty."}
                    </p>
                  </div>
                ) : (
                  <>
                    {emails.map((e) => (
                      <EmailRow
                        key={e.id}
                        email={e}
                        active={selected?.id === e.id}
                        onClick={() => openEmail(e.id)}
                      />
                    ))}
                    {nextToken && (
                      <div className="p-3 text-center">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={loadMore}
                          disabled={loadingMore}
                        >
                          {loadingMore && (
                            <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                          )}
                          Load more
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            {/* Detail */}
            <Card className="flex min-h-[420px] flex-col overflow-hidden">
              {detailLoading ? (
                <div className="flex flex-1 items-center justify-center">
                  <Loader2 className="size-6 animate-spin text-muted-foreground" />
                </div>
              ) : selected ? (
                <>
                  <div className="border-b border-border p-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mb-2 -ml-2 md:hidden"
                      onClick={() => setSelected(null)}
                    >
                      <ArrowLeft className="size-4" /> Back
                    </Button>
                    <h2 className="text-base font-semibold leading-snug">
                      {selected.subject}
                    </h2>
                    <div className="mt-2 flex items-center justify-between gap-3 text-sm">
                      <div className="min-w-0">
                        <p className="truncate font-medium">
                          {selected.sender_name || selected.sender_email}
                        </p>
                        <p className="truncate text-xs text-muted-foreground">
                          {selected.sender_email}
                          {selected.to.length > 0 &&
                            ` → ${selected.to.map((t) => t.address).join(", ")}`}
                        </p>
                      </div>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {selected.received_at &&
                          new Date(selected.received_at).toLocaleString()}
                      </span>
                    </div>
                    {selected.attachments.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {selected.attachments.map((a) => (
                          <Badge
                            key={a}
                            variant="outline"
                            className="max-w-48 truncate text-xs"
                          >
                            <Paperclip className="mr-1 size-3" />
                            {a}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <ScrollArea className="flex-1 p-4">
                    {selected.body_text ? (
                      <pre className="font-sans text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">
                        {selected.body_text}
                      </pre>
                    ) : selected.body_html_sanitized ? (
                      // Sanitized server-side (allowlist); never raw email HTML.
                      <div
                        className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed [&_a]:text-primary"
                        dangerouslySetInnerHTML={{
                          __html: selected.body_html_sanitized,
                        }}
                      />
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        This email has no readable body.
                      </p>
                    )}
                  </ScrollArea>
                </>
              ) : (
                <div className="flex flex-1 flex-col items-center justify-center gap-2 p-8 text-center">
                  <Mail className="size-8 text-muted-foreground/50" />
                  <p className="text-sm text-muted-foreground">
                    Select an email to read it.
                  </p>
                </div>
              )}
            </Card>
          </div>
        )}

        {error && emails.length > 0 && (
          <p className="mt-3 text-sm text-destructive">{error}</p>
        )}
      </div>
    </AppShell>
  );
}
