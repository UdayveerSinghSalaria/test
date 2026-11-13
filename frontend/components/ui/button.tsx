"use client";

import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "destructive" | "outline" | "default";
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className = "", children, disabled, ...props }, ref) => {
    const base = "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
    
    const variants: Record<string, string> = {
      primary: "bg-gradient-to-r from-brand-600 to-brand-700 text-white shadow hover:from-brand-700 hover:to-brand-800",
      secondary: "bg-white/80 hover:bg-brand-50 text-ink/80 border border-brand-200 dark:bg-white/10 dark:hover:bg-brand-900/20 dark:border-brand-800 dark:text-ink",
      ghost: "text-ink/70 hover:bg-brand-100 transition dark:text-ink/80 dark:hover:bg-brand-900/30",
      destructive: "bg-rose-600 text-white hover:bg-rose-700",
      outline: "bg-transparent border border-brand-200 text-brand-700 hover:bg-brand-50 dark:border-brand-800 dark:text-brand-300",
      default: "bg-gradient-to-r from-brand-600 to-brand-700 text-white shadow hover:from-brand-700 hover:to-brand-800",
    };

    const sizes: Record<string, string> = {
      sm: "px-3 py-1.5 text-sm",
      md: "px-4 py-2 text-sm",
      lg: "px-6 py-3 text-base",
    };

    return (
      <button
        ref={ref}
        className={`${base} ${variants[variant] || variants.primary} ${sizes[size]} ${className}`}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";