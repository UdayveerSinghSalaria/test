"use client";

import React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  className?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="space-y-1">
        {label && <label htmlFor={inputId} className="block text-sm font-semibold">{label}</label>}
        <input
          ref={ref}
          id={inputId}
          className={`rounded-xl border border-brand-200 bg-white/80 px-3 py-2 text-sm outline-none
            focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500
            dark:bg-white/10 dark:border-brand-800 dark:focus:ring-brand-500/20
            ${error ? "border-rose-500" : ""} ${className}`}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...props}
        />
        {error && <p id={`${inputId}-error`} className="text-xs text-rose-600 dark:text-rose-400">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  className?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className = "", id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="space-y-1">
        {label && <label htmlFor={inputId} className="block text-sm font-semibold">{label}</label>}
        <textarea
          ref={ref}
          id={inputId}
          className={`rounded-xl border border-brand-200 bg-white/80 px-3 py-2 text-sm outline-none resize-none
            focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500
            dark:bg-white/10 dark:border-brand-800 dark:focus:ring-brand-500/20
            ${error ? "border-rose-500" : ""} ${className}`}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...props}
        />
        {error && <p id={`${inputId}-error`} className="text-xs text-rose-600 dark:text-rose-400">{error}</p>}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  className?: string;
  options: { value: string; label: string }[];
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, className = "", options, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="space-y-1">
        {label && <label htmlFor={inputId} className="block text-sm font-semibold">{label}</label>}
        <select
          ref={ref}
          id={inputId}
          className={`rounded-xl border border-brand-200 bg-white/80 px-3 py-2 text-sm outline-none
            focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500
            dark:bg-white/10 dark:border-brand-800 dark:focus:ring-brand-500/20
            ${error ? "border-rose-500" : ""} ${className}`}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...props}
        >
          {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
        </select>
        {error && <p id={`${inputId}-error`} className="text-xs text-rose-600 dark:text-rose-400">{error}</p>}
      </div>
    );
  }
);
Select.displayName = "Select";