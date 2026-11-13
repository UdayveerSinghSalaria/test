"use client";

import React from "react";
import { X } from "lucide-react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";

export const AppShell = ({ children }: { children: React.ReactNode }) => {
  const [mobileOpen, setMobileOpen] = React.useState(false);

  return (
    <div className="min-h-screen">
      <Sidebar />
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-ink/30" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 bg-white/95 backdrop-blur-xl">
            <button className="absolute right-3 top-3" onClick={() => setMobileOpen(false)} aria-label="Close menu">
              <X />
            </button>
            <Sidebar />
          </aside>
        </div>
      )}
      <div className="lg:pl-64">
        <Header />
        <main className="px-4 pb-10 md:px-8">{children}</main>
      </div>
    </div>
  );
};