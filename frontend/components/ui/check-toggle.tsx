"use client";

import React from "react";
import { Check } from "lucide-react";

interface CheckToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  className?: string;
  "aria-label"?: string;
}

export const CheckToggle = ({ checked, onChange, className = "", "aria-label": ariaLabel }: CheckToggleProps) => (
  <button
    onClick={() => onChange(!checked)}
    aria-label={ariaLabel || (checked ? "Mark incomplete" : "Mark complete")}
    className={`grid h-6 w-6 shrink-0 place-items-center rounded-md border-2 transition ${className} ${
      checked ? "border-brand-600 bg-brand-600 text-white" : "border-brand-200 bg-white hover:border-brand-500 dark:bg-white/10 dark:border-brand-800"
    }`}
  >
    {checked && <Check size={14} />}
  </button>
);