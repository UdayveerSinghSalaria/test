/**
 * Central application configuration.
 *
 * The product name is TEMPORARY and configurable: change APP_NAME here (or
 * override NEXT_PUBLIC_APP_NAME in .env.local) to rebrand without touching
 * any component. No logo or permanent branding exists yet, by design.
 */

export const APP_NAME =
  process.env.NEXT_PUBLIC_APP_NAME ?? "SaarthiFlow";

/**
 * Backend base URL.
 *
 * Empty string (default) = same origin: requests hit the Next.js /api
 * rewrite proxy, which forwards to FastAPI. This keeps the httpOnly session
 * cookie same-site. Set NEXT_PUBLIC_API_URL only for direct cross-origin
 * setups (then CORS on the backend must allow this origin).
 */
export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

/** Sidebar navigation — single source of truth for the app shell. */
export const NAV_SECTIONS: { label: string; items: NavItem[] }[] = [
  {
    label: "",
    items: [
      { href: "/", label: "Overview", icon: "LayoutDashboard" },
      { href: "/agent", label: "Agent Studio", icon: "Sparkles" },
      { href: "/space", label: "My Space", icon: "ListTodo" },
      { href: "/approvals", label: "Approvals", icon: "ShieldCheck" },
      { href: "/activity", label: "Activity", icon: "History" },
    ],
  },
  {
    label: "Tools",
    items: [
      { href: "/calendar", label: "Calendar", icon: "Calendar" },
      { href: "/quick-actions", label: "Quick Actions", icon: "Zap" },
      { href: "/analytics", label: "Analytics", icon: "BarChart3" },
    ],
  },
  {
    label: "Configuration",
    items: [
      { href: "/settings", label: "Settings", icon: "Settings" },
      { href: "/extension", label: "Get Extension", icon: "Puzzle" },
    ],
  },
];

export interface NavItem {
  href: string;
  label: string;
  icon: string;
  badge?: string;
}