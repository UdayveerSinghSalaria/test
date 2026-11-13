"use client";

import { useCallback, useEffect, useRef, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  CircleDashed,
  Loader2,
  Send,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { apiStream } from "@/lib/api";
import type { AgentStep } from "@/types";

interface LogEntry {
  key: number;
  step: AgentStep;
}

const STEP_META: Record<
  AgentStep["type"],
  { icon: React.ElementType; label: string; className?: string }
> = {
  plan: { icon: CircleDashed, label: "Planning" },
  tool_start: { icon: Wrench, label: "Using tool" },
  tool_result: { icon: CheckCircle2, label: "Tool result" },
  approval_required: { icon: ShieldCheck, label: "Approval needed" },
  answer: { icon: Sparkles, label: "Answer" },
  error: { icon: AlertTriangle, label: "Error" },
};

export default function AssistantPage() {
  return (
    <Suspense fallback={null}>
      <AssistantInner />
    </Suspense>
  );
}

function AssistantInner() {
  const params = useSearchParams();
  const [input, setInput] = useState("");
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [answer, setAnswer] = useState("");
  const [queued, setQueued] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const keyRef = useRef(0);

  const run = useCallback(async (instruction: string) => {
    if (!instruction.trim() || running) return;
    setRunning(true);
    setAnswer("");
    setLog([]);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      for await (const raw of apiStream(
        "/api/assistant/run",
        { message: instruction },
        controller.signal
      )) {
        const step = raw as unknown as AgentStep;
        keyRef.current += 1;
        setLog((prev) => [...prev, { key: keyRef.current, step }]);
        if (step.type === "answer") setAnswer(step.text);
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        keyRef.current += 1;
        setLog((prev) => [
          ...prev,
          {
            key: keyRef.current,
            step: {
              type: "error",
              text: err instanceof Error ? err.message : "Assistant run failed.",
              tool: "",
              detail: "",
              approval_id: null,
            },
          },
        ]);
      }
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }, [running]);

  // Support ?q=… deep links (from the dashboard quick action).
  useEffect(() => {
    const q = params.get("q");
    if (q && !running && log.length === 0) {
      setQueued(q);
      setInput("");
      run(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log, answer]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || running) return;
    setInput("");
    run(text);
  };

  const stop = () => abortRef.current?.abort();

  return (
    <AppShell>
      <div className="mx-auto flex h-full max-w-3xl flex-col px-4 py-6 md:px-6">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">AI Assistant</h1>
            <p className="text-sm text-muted-foreground">
              Give it an instruction — watch the plan, tool calls, and result as
              they happen.
            </p>
          </div>
        </div>

        {/* Execution log */}
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto rounded-lg border border-border bg-card p-4">
          {log.length === 0 && !running && (
            <div className="flex h-full min-h-56 flex-col items-center justify-center gap-3 text-center">
              <div className="flex size-10 items-center justify-center rounded-full border border-border">
                <Sparkles className="size-5 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Nothing running yet</p>
                <p className="max-w-sm text-xs text-muted-foreground">
                  Try: “search my inbox for emails from my boss”, “what&apos;s
                  unread?”, or “list my tasks”.
                </p>
              </div>
            </div>
          )}

          {log.map(({ key, step }) => {
            const meta = STEP_META[step.type] ?? STEP_META.tool_result;
            const Icon = meta.icon;
            return (
              <div key={key} className="flex items-start gap-2.5 text-sm">
                <Icon
                  className={`mt-0.5 size-4 shrink-0 ${
                    step.type === "error"
                      ? "text-destructive"
                      : step.type === "approval_required"
                        ? "text-amber-500"
                        : step.type === "answer"
                          ? "text-primary"
                          : "text-muted-foreground"
                  }`}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">{meta.label}</span>
                    {step.tool && (
                      <Badge variant="outline" className="text-xs">
                        {step.tool}
                      </Badge>
                    )}
                  </div>
                  {step.text && step.type !== "answer" && (
                    <p className="mt-0.5 break-words text-muted-foreground">
                      {step.text}
                    </p>
                  )}
                  {step.type === "tool_result" && (
                    <p className="mt-0.5 text-xs text-muted-foreground/70">
                      {step.detail === "error" ? "failed" : "completed"}
                    </p>
                  )}
                  {step.type === "approval_required" && (
                    <div className="mt-1.5 flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          window.location.href = "/approvals";
                        }}
                      >
                        Review in Approvals
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {running && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Working…
            </div>
          )}

          {answer && (
            <div className="rounded-md border border-border bg-muted/40 p-3">
              <div className="mb-1.5 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                <Sparkles className="size-3.5" /> Response
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {answer}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Composer */}
        <form onSubmit={submit} className="mt-4 space-y-2">
          <div className="flex items-end gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit(e);
                }
              }}
              placeholder="Ask the assistant to read, search, or summarize your email…"
              rows={2}
              className="min-h-16 flex-1 resize-none"
              disabled={running}
            />
            {running ? (
              <Button type="button" variant="destructive" onClick={stop}>
                Stop
              </Button>
            ) : (
              <Button type="submit" disabled={!input.trim()}>
                <Send className="size-4" /> Send
              </Button>
            )}
          </div>
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <ChevronRight className="size-3" />
            Reading is automatic; anything that changes your data asks first.
          </p>
        </form>
      </div>
    </AppShell>
  );
}
