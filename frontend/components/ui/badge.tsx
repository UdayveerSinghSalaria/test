"use client";

import React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "high" | "medium" | "low" | "brand" | "secondary" | "outline" | "destructive";
  capitalize?: boolean;
  className?: string;
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = "default", capitalize = false, className = "", children, ...props }, ref) => {
    const variants: Record<string, string> = {
      default: "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300",
      high: "bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400",
      medium: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
      low: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
      brand: "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300",
      secondary: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
      outline: "bg-transparent border border-brand-200 text-brand-700 dark:border-brand-800 dark:text-brand-300",
      destructive: "bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400",
    };

    const displayChildren = capitalize && typeof children === "string" ? children.charAt(0).toUpperCase() + children.slice(1) : children;

    return (
      <span
        ref={ref}
        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${variants[variant]} ${className}`}
        {...props}
      >
        {displayChildren}
      </span>
    );
  }
);
Badge.displayName = "Badge";

export const PriorityBadge = ({ priority }: { priority: "High" | "Medium" | "Low" }) => (
  <Badge variant={priority.toLowerCase() as "high" | "medium" | "low"}>{priority}</Badge>
);

export const StatusBadge = ({ status }: { status: string }) => {
  const variant = status === "pending" ? "medium" : status === "approved" ? "low" : status === "rejected" ? "high" : "default";
  return <Badge variant={variant as any} capitalize>{status}</Badge>;
};