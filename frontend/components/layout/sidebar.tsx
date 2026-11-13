"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Bot,
  FolderKanban,
  CheckSquare,
  Activity as Act,
  CalendarDays,
  Zap,
  BarChart3,
  Settings as Cog,
  Puzzle,
  Search,
  Bell,
  Menu,
  X,
  ChevronDown,
  Zap as ZapIcon,
} from "lucide-react";
import { useApp } from "@/context/app-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const mainNav = [
  ["/", "Overview", Home] as const,
  ["/agent", "Agent Studio", Bot] as const,
  ["/space", "My Space", FolderKanban] as const,
  ["/approvals", "Approvals", CheckSquare] as const,
  ["/activity", "Activity", Act] as const,
];

const toolsNav = [
  ["/calendar", "Calendar View", CalendarDays] as const,
  ["/quick-actions", "Quick Actions", Zap] as const,
  ["/analytics", "Analytics", BarChart3] as const,
];

const footerNav = [
  ["/settings", "Settings", Cog] as const,
  ["/extension", "Get Extension", Puzzle] as const,
];

export const Sidebar = () => {
  const { proposals } = useApp();
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);
  const [q, setQ] = React.useState("");

  const pend = proposals.filter(p => p.status === "pending").length;

  React.useEffect(() => {
    setOpen(false);
    window.scrollTo(0, 0);
  }, [pathname]);

  const NavItem = ({ to, label, Icon, badge }: { to: string; label: string; Icon: React.ElementType; badge?: React.ReactNode }) => (
    <Link
      key={to}
      href={to}
      className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] font-medium transition ${
        pathname === to
          ? "text-white shadow-lg"
          : "text-ink/80 hover:bg-white/70 dark:text-ink/400 dark:hover:bg-white/10"
      }`}
      style={pathname === to ? { background: "linear-gradient(135deg,#a78bfa,#8b5cf6)" } : {}}
    >
      <Icon size={20} />
      {label}
      {badge}
    </Link>
  );

  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-white/70 bg-white/50 backdrop-blur-xl lg:block">
      <div className="flex h-full flex-col gap-1 p-4">
        <div className="mb-5 flex items-center gap-2 px-2">
          <div className="grid h-10 w-10 place-items-center rounded-2xl text-white" style={{ background: "linear-gradient(135deg,#8b5cf6,#6d28d9)" }}>
            <ZapIcon size={22} />
          </div>
          <div>
            <div className="text-xl font-extrabold italic leading-5">SaarthiFlow</div>
            <div className="text-xs text-ink/60">From Browsing to Doing</div>
          </div>
        </div>
        {mainNav.map(([to, label, Icon]) => (
          <NavItem key={to} to={to} label={label} Icon={Icon} />
        ))}
        <div className="mt-4 border-t border-brand-100 px-3 pb-1 pt-4 text-sm font-semibold text-ink/60">Tools</div>
        {toolsNav.map(([to, label, Icon]) => (
          <NavItem key={to} to={to} label={label} Icon={Icon} />
        ))}
        <div className="mt-auto space-y-1">
          {footerNav.map(([to, label, Icon]) => (
            <NavItem key={to} to={to} label={label} Icon={Icon} />
          ))}
        </div>
      </div>
    </aside>
  );
};