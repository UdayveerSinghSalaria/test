"use client";

import React from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Search, Bell, ChevronDown, Menu, X } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { useApp } from "@/context/app-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";

export const Header = () => {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, logout } = useAuth();
  const { proposals } = useApp();
  const [open, setOpen] = React.useState(false);
  const [q, setQ] = React.useState(searchParams?.get("q") || "");

  const pend = proposals.filter(p => p.status === "pending").length;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    router.push("/space?q=" + encodeURIComponent(q));
  };

  return (
    <header className="sticky top-0 z-20 flex items-center gap-3 px-4 py-3 md:px-8 bg-white/50 backdrop-blur-xl border-b border-white/70">
      <Button variant="ghost" size="sm" className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
        <Menu />
      </Button>
      <form className="glass !rounded-full ml-auto flex max-w-md flex-1 items-center gap-2 px-4 py-2" onSubmit={handleSearch}>
        <Search size={18} className="text-ink/50" />
        <Input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Search tasks..."
          className="w-full min-w-[140px] bg-transparent py-2 text-sm outline-none"
        />
      </form>
      <Button variant="ghost" size="sm" onClick={() => router.push("/approvals")} aria-label="Approvals">
        <Bell size={20} />
        {pend > 0 && <span className="absolute right-2 top-2 h-2.5 w-2.5 rounded-full bg-brand-500" />}
      </Button>
      <Link href="/settings" className="flex items-center gap-1">
        <span className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-brand-400 to-brand-700 font-bold text-white">
          {user?.name?.[0] || user?.email?.[0]?.toUpperCase() || "U"}
        </span>
        <ChevronDown size={16} />
      </Link>
    </header>
  );
}