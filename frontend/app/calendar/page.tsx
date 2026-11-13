import { AppShell } from "@/components/layout/app-shell";
import { Calendar, Construction } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

/**
 * Calendar — PLACEHOLDER (not functional).
 * Google Calendar API architecture is planned for a later milestone; this
 * page says so explicitly instead of showing mock events.
 */
export default function CalendarPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-5 px-4 py-6 md:px-6">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Calendar</h1>
          <p className="text-sm text-muted-foreground">
            Events, conflicts, and scheduling.
          </p>
        </div>

        <Card className="border-dashed">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-lg border border-border bg-muted/40">
                <Calendar className="size-5 text-muted-foreground" />
              </div>
              <div>
                <CardTitle className="flex items-center gap-2 text-base">
                  Google Calendar
                  <Badge variant="secondary">Not implemented</Badge>
                </CardTitle>
                <CardDescription>
                  <Construction className="mr-1 inline size-3.5" />
                  Architecture prepared, API not wired up yet.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            <p>
              Calendar integration ships after the Gmail milestone. Nothing on
              this page is simulated — once the API is connected, real events
              will appear here.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
