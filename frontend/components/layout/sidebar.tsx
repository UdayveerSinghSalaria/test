"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Sparkles,
  ListTodo,
  Inbox,
  Calendar,
  ShieldCheck,
  History,
  Plug,
  Settings,
  type LucideIcon,
} from "lucide-react";
import { APP_NAME, NAV_SECTIONS } from "@/lib/config";
import { cn } from "@/lib/utils";

const ICONS: Record<string, LucideIcon> = {
  LayoutDashboard,
  Sparkles,
  ListTodo,
  Inbox,
  Calendar,
  ShieldCheck,
  History,
  Plug,
  Settings,
};

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-sidebar md:flex">
      {/* Brand — temporary neutral title, driven by central config */}
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Sparkles className="size-3.5" />
        </div>
        <span className="text-sm font-semibold tracking-tight">{APP_NAME}</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {NAV_SECTIONS.map((section, i) => (
          <div key={section.label || i} className="mb-4">
            {section.label && (
              <div className="mb-1 px-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
                {section.label}
              </div>
            )}
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = ICONS[item.icon];
                const active =
                  pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "group flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors",
                        active
                          ? "bg-accent font-medium text-accent-foreground"
                          : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                      )}
                    >
                      {Icon && (
                        <Icon
                          className={cn(
                            "size-4 shrink-0 transition-colors",
                            active ? "text-foreground" : "text-muted-foreground group-hover:text-foreground"
                          )}
                        />
                      )}
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.badge && (
                        <span className="rounded border border-border px-1 py-px text-[10px] uppercase text-muted-foreground">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-border px-4 py-3">
        <p className="text-[11px] leading-relaxed text-muted-foreground/70">
          MVP preview — Gmail integration active, Calendar &amp; agent execution
          landing next.
        </p>
      </div>
    </aside>
  );
}
