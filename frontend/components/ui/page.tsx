"use client";

import React from "react";

export interface PageProps {
  title: string;
  sub?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Page = ({ title, sub, right, children, className = "" }: PageProps) => (
  <div className={`space-y-5 ${className}`}>
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-extrabold">{title}</h1>
        {sub && <p className="text-sm text-ink/60 dark:text-ink/400">{sub}</p>}
      </div>
      {right}
    </div>
    {children}
  </div>
);

export const Empty = ({ text }: { text: string }) => (
  <p className="rounded-2xl border border-dashed border-brand-200 p-6 text-center text-sm text-ink/50 dark:text-ink/400 dark:border-brand-800">
    {text}
  </p>
);

export const Title = ({ icon: Icon, children, right }: { icon?: React.ElementType; children: React.ReactNode; right?: React.ReactNode }) => (
  <div className="mb-4 flex items-center justify-between">
    <h3 className="flex items-center gap-2 text-lg font-bold">
      {Icon && <Icon size={20} className="text-brand-600" />}
      {children}
    </h3>
    {right}
  </div>
);