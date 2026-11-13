# SaarthiFlow Frontend Integration Plan

## Executive Summary
Integrate the SaarthiFlow Vite/React frontend into the existing **AI Work Assistant** (Next.js 16 + FastAPI + PostgreSQL/Supabase) codebase, replacing the current Next.js pages with the SaarthiFlow design system and UX, while connecting to the existing backend APIs.

**Target**: Single unified app at `C:\Users\asus\Projects\AI_Proj1` with SaarthiFlow UI + existing backend.

---

## Current State Analysis

### AI Work Assistant (Host Project)
| Layer | Tech |
|-------|------|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind v4, shadcn/ui, Lucide |
| Backend | FastAPI, Pydantic, SQLAlchemy 2, LangGraph, PostgreSQL/Supabase (SQLite dev) |
| Auth | Email/password (argon2) + Google OAuth 2.0 (httpOnly cookies, CSRF state) |
| APIs | `/api/auth/*`, `/api/emails`, `/api/tasks`, `/api/approvals`, `/api/activity`, `/api/integrations/*`, `/api/assistant` (streaming) |
| State | Server-first (React Server Components), no client state lib |

### SaarthiFlow (Source Frontend)
| Layer | Tech |
|-------|------|
| Frontend | Vite 5, React 18, React Router 6, Tailwind v3, Lucide React, Recharts |
| State | React Context + localStorage (`sf-v1` key), no server |
| Pages | Overview, Agent Studio, My Space, Approvals, Activity, Calendar, Quick Actions, Analytics, Settings, Extension |
| Data | Demo-seeded, all local (no API calls) |
| Design | Glassmorphism, brand purple (#8b5cf6), Plus Jakarta Sans font |

---

## Integration Strategy

**Approach**: Progressive migration — keep Next.js as host, replace page-by-page with SaarthiFlow components, connect to existing FastAPI endpoints.

### Phase 0: Foundation (1-2 days)
- [ ] Add Tailwind v3 config alongside v4 (or migrate design tokens to v4)
- [ ] Add Plus Jakarta Sans font to `frontend/app/layout.tsx`
- [ ] Create shared design token file (colors, spacing, glassmorphism utilities)
- [ ] Set up React Context provider pattern compatible with Next.js Client Components
- [ ] Install Recharts (`npm i recharts`)

### Phase 1: Core Layout & Navigation (2 days)
- [ ] **Sidebar** → `frontend/components/layout/sidebar.tsx` (collapsible, mobile drawer)
- [ ] **Header** → `frontend/components/layout/header.tsx` (search, notifications, user avatar)
- [ ] **AppShell** → `frontend/components/layout/app-shell.tsx` (replaces current layout)
- [ ] **Routing** → Map SaarthiFlow routes to Next.js App Router:
  - `/` → Overview (Dashboard)
  - `/agent` → Agent Studio
  - `/space` → My Space (Tasks)
  - `/approvals` → Approvals
  - `/activity` → Activity
  - `/calendar` → Calendar
  - `/quick-actions` → Quick Actions
  - `/analytics` → Analytics
  - `/settings` → Settings
  - `/extension` → Extension (placeholder)

### Phase 2: State & API Layer (2 days)
- [ ] **API Client** → Extend `frontend/lib/api.ts` with SaarthiFlow endpoints
- [ ] **Auth Context** → Wrap existing session auth for client components
- [ ] **App Context** → `frontend/context/app-context.tsx` mirroring `store.jsx`:
  - `tasks`, `proposals`, `activity`, `settings`
  - `addTask`, `updateTask`, `deleteTask`, `toggleTask`
  - `addProposal`, `decideProposal`
  - `saveSettings`, `resetData`
  - Persist to localStorage **and** sync to backend via API
- [ ] **TanStack Query / SWR** → For server state (tasks, proposals, activity)

### Phase 3: Page Components (4-5 days)

| Page | Source | Backend Integration | Notes |
|------|--------|---------------------|-------|
| **Overview** | `Overview` | `/api/tasks`, `/api/activity`, `/api/approvals` | KPI cards, recent tasks, charts |
| **Agent Studio** | `Agent` | `/api/assistant` (streaming) | Replace simulated AI with real LangGraph agent |
| **My Space** | `Space` | `/api/tasks` (CRUD) | List + Kanban views, filters, search |
| **Approvals** | `Approvals` | `/api/approvals` | Pending/approved/rejected tabs |
| **Activity** | `ActivityPage` | `/api/activity` | Filterable timeline |
| **Calendar** | `CalendarPage` | `/api/tasks` | Month view with task dots |
| **Quick Actions** | `Quick` | `/api/assistant` | Pre-filled agent commands |
| **Analytics** | `Analytics` | `/api/tasks`, `/api/activity` | Recharts visualizations |
| **Settings** | `SettingsPage` | `/api/auth/me`, `/api/integrations/*` | Profile, preferences, reset |
| **Extension** | `Extension` | — | Placeholder (Coming Soon) |

### Phase 4: UI Components Library (2 days)
Extract reusable components from `ui.jsx` → `frontend/components/ui/`:
- `Card`, `Title`, `Pri` (priority chip), `Modal`, `Page`, `Empty`, `TaskModal`
- `Check_` (checkbox toggle), `Donut` (pie chart wrapper)
- Glassmorphism utilities: `glass`, `glass rise`, `hov`, `btn`, `btn2`, `inp`, `chip`

### Phase 5: Backend Alignment (1-2 days)
- [ ] Ensure `/api/tasks` supports: `GET` (list), `POST` (create), `PATCH` (update), `DELETE`
- [ ] Ensure `/api/approvals` supports: `GET` (list), `POST` (decide), `PATCH` (update proposal tasks)
- [ ] Add `/api/activity` with filtering
- [ ] Add `/api/assistant` streaming endpoint compatibility
- [ ] Verify `/api/integrations/activepieces/status` works

### Phase 6: Polish & Migration (2 days)
- [ ] Replace all current Next.js pages (`frontend/app/*/page.tsx`) with new components
- [ ] Remove old shadcn/ui dependencies no longer needed
- [ ] Update `frontend/lib/config.ts` with SaarthiFlow branding (`APP_NAME = "SaarthiFlow"`)
- [ ] Test all flows end-to-end: auth → tasks → agent → approvals → activity
- [ ] Update README with new routes and features

---

## Detailed Component Mapping

### 1. Layout Components
```
frontend/components/layout/
├── app-shell.tsx          # Main wrapper (sidebar + header + main)
├── sidebar.tsx            # Collapsible nav with badge counts
├── sidebar-mobile.tsx     # Mobile drawer
├── header.tsx             # Search, notifications, user menu
└── user-menu.tsx          # Avatar dropdown (settings, logout)
```

### 2. Context & Hooks
```
frontend/context/
├── app-context.tsx        # Global state (tasks, proposals, activity, settings)
├── auth-context.tsx       # Session user, login/logout
└── index.ts               # Exports

frontend/hooks/
├── use-tasks.ts           # TanStack Query hooks for tasks
├── use-proposals.ts       # Proposals + approval mutations
├── use-activity.ts        # Activity log
├── use-settings.ts        # User settings
└── use-agent.ts           # Agent streaming chat
```

### 3. Pages (App Router)
```
frontend/app/
├── page.tsx               # Overview (Dashboard)
├── agent/page.tsx         # Agent Studio
├── space/page.tsx         # My Space
├── approvals/page.tsx     # Approvals
├── activity/page.tsx      # Activity
├── calendar/page.tsx      # Calendar
├── quick-actions/page.tsx # Quick Actions
├── analytics/page.tsx     # Analytics
├── settings/page.tsx      # Settings
└── extension/page.tsx     # Extension
```

### 4. Feature Components
```
frontend/components/
├── overview/
│   ├── kpi-cards.tsx
│   ├── agent-command.tsx
│   ├── task-list.tsx
│   ├── weekly-chart.tsx
│   ├── activity-timeline.tsx
│   └── upcoming-deadlines.tsx
├── agent/
│   ├── chat-interface.tsx
│   ├── plan-stepper.tsx
│   ├── proposed-tasks.tsx
│   └── quick-prompts.tsx
├── space/
│   ├── task-list.tsx
│   ├── task-kanban.tsx
│   ├── task-row.tsx
│   ├── project-progress.tsx
│   └── filters.tsx
├── approvals/
│   ├── proposal-card.tsx
│   ├── proposal-tasks.tsx
│   └── approval-actions.tsx
├── activity/
│   └── activity-timeline.tsx
├── calendar/
│   ├── month-grid.tsx
│   └── day-detail.tsx
├── analytics/
│   ├── stat-cards.tsx
│   ├── weekly-bar.tsx
│   ├── priority-donut.tsx
│   └── project-progress.tsx
└── settings/
    ├── profile-form.tsx
    ├── preferences.tsx
    └── danger-zone.tsx
```

### 5. UI Primitives (shadcn/ui + custom)
```
frontend/components/ui/
├── card.tsx               # Glassmorphism Card
├── button.tsx             # btn, btn2 variants
├── input.tsx              # inp variant
├── select.tsx             # inp variant
├── badge.tsx              # chip, priority chips
├── modal.tsx              # Modal with backdrop
├── checkbox.tsx           # Check_ toggle
├── avatar.tsx             # User avatar
├── dropdown-menu.tsx      # User menu
├── tabs.tsx               # Approval tabs
├── tooltip.tsx
└── chart/                 # Recharts wrappers
    ├── bar-chart.tsx
    ├── area-chart.tsx
    ├── pie-chart.tsx
    └── donut-chart.tsx
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      NEXT.JS APP (CLIENT)                       │
├─────────────────────────────────────────────────────────────────┤
│  AppContext (React Context)                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Tasks     │ │ Proposals   │ │  Activity   │ │ Settings  │ │
│  │  (CRUD)     │ │ (Approval)  │ │  (Log)      │ │ (Profile) │ │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬─────┘ │
│         │               │               │               │       │
│         ▼               ▼               ▼               ▼       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              TanStack Query / SWR Cache                  │   │
│  │  (server state, background refetch, optimistic updates)  │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │               │               │               │       │
│         ▼               ▼               ▼               ▼       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              API Client (frontend/lib/api.ts)            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼ (HTTP/JSON, SSE for agent)
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
├─────────────────────────────────────────────────────────────────┤
│  /api/tasks       /api/approvals    /api/activity   /api/auth  │
│  /api/integrations/*  /api/assistant (SSE streaming)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Technical Decisions

### 1. Tailwind Version
**Decision**: Keep Tailwind v4 (current) and migrate SaarthiFlow design tokens.
- Add `brand` colors to `frontend/app/globals.css` using `@theme`
- Convert `glass`, `glass rise`, `hov`, `btn`, `btn2`, `inp`, `chip` to v4 utilities

### 2. State Management
**Decision**: React Context + TanStack Query (not Redux/Zustand).
- Context for client-only state (UI modals, form drafts)
- TanStack Query for all server state (tasks, proposals, activity)
- localStorage only for offline-first demo data fallback

### 3. TypeScript
**Decision**: Full TypeScript — create types mirroring backend Pydantic schemas.
```
frontend/types/
├── task.ts          # Task, TaskCreate, TaskUpdate
├── proposal.ts      # Proposal, ProposalDecision
├── activity.ts      # ActivityEntry
├── settings.ts      # UserSettings
└── api.ts           # ApiResponse, PaginatedResponse
```

### 4. Agent Integration
**Decision**: Replace SaarthiFlow's simulated `makePlan()` with real `/api/assistant` streaming.
- Keep the same chat UI (`msgs`, `plan`, `stages` stepper)
- On "Send for Approval" → POST `/api/approvals` with proposal payload
- Approval decision → PATCH `/api/approvals/:id` → creates real tasks

### 5. Routing
**Decision**: Next.js App Router (not React Router).
- Each page = `page.tsx` in route segment
- Client Components for interactive pages (`"use client"`)
- Search params via `useSearchParams()` hook

---

## Migration Checklist

### Files to Create
- [ ] `frontend/app/globals.css` — Tailwind v4 theme + glassmorphism utilities
- [ ] `frontend/context/app-context.tsx` — Global state provider
- [ ] `frontend/context/auth-context.tsx` — Auth state provider
- [ ] `frontend/hooks/use-tasks.ts` — Task queries/mutations
- [ ] `frontend/hooks/use-proposals.ts` — Proposal queries/mutations
- [ ] `frontend/hooks/use-activity.ts` — Activity queries
- [ ] `frontend/hooks/use-agent.ts` — Agent streaming
- [ ] `frontend/types/*.ts` — TypeScript interfaces
- [ ] `frontend/components/ui/*.tsx` — 15+ UI primitives
- [ ] `frontend/components/layout/*.tsx` — AppShell, Sidebar, Header
- [ ] `frontend/app/*/page.tsx` — 10 page components
- [ ] `frontend/components/overview/*.tsx` — Dashboard widgets
- [ ] `frontend/components/agent/*.tsx` — Agent Studio
- [ ] `frontend/components/space/*.tsx` — My Space
- [ ] `frontend/components/approvals/*.tsx` — Approvals
- [ ] `frontend/components/analytics/*.tsx` — Charts

### Files to Modify
- [ ] `frontend/package.json` — Add `recharts`, `@tanstack/react-query`
- [ ] `frontend/tsconfig.json` — Path aliases for `@/components`, `@/hooks`, `@/context`
- [ ] `frontend/app/layout.tsx` — Add providers, font, global styles
- [ ] `frontend/app/providers.tsx` — Context providers wrapper
- [ ] `frontend/lib/api.ts` — Add SaarthiFlow endpoints
- [ ] `frontend/lib/config.ts` — Update `APP_NAME = "SaarthiFlow"`

### Files to Remove (after migration)
- [ ] Old `frontend/app/dashboard/page.tsx`
- [ ] Old `frontend/app/inbox/page.tsx`
- [ ] Old `frontend/app/calendar/page.tsx` (placeholder)
- [ ] Old `frontend/app/assistant/page.tsx`
- [ ] Old `frontend/app/tasks/page.tsx`
- [ ] Old `frontend/app/approvals/page.tsx`
- [ ] Old `frontend/app/activity/page.tsx`
- [ ] Old `frontend/app/settings/page.tsx`
- [ ] Old shadcn/ui components no longer used

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tailwind v3→v4 migration breaks design | High | Build design token file first; test in Storybook/isolated page |
| React Router → Next.js Router differences | Medium | Use `useSearchParams`, `usePathname` hooks; test deep links |
| localStorage vs Server sync conflicts | Medium | Server wins on conflict; localStorage only for offline demo |
| Agent streaming SSE compatibility | High | Test `/api/assistant` with real backend before UI integration |
| Recharts SSR issues | Low | Wrap charts in dynamic import with `ssr: false` |
| TypeScript errors from JSX migration | Medium | Incremental `any` → proper types; strict mode at end |

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Foundation | 1-2 days | 2 days |
| Phase 1: Layout & Navigation | 2 days | 4 days |
| Phase 2: State & API Layer | 2 days | 6 days |
| Phase 3: Page Components | 4-5 days | 11 days |
| Phase 4: UI Components | 2 days | 13 days |
| Phase 5: Backend Alignment | 1-2 days | 15 days |
| Phase 6: Polish & Migration | 2 days | 17 days |
| **Total** | | **~3-4 weeks** |

---

## Immediate Next Steps

1. **Create design token file** — Extract SaarthiFlow colors, spacing, glassmorphism to `frontend/app/globals.css`
2. **Install dependencies** — `npm i recharts @tanstack/react-query lucide-react` (already have lucide)
3. **Build AppShell** — Sidebar + Header + routing structure
4. **Implement AppContext** — Mirror `store.jsx` API with TypeScript
5. **Connect one page end-to-end** — Start with **Overview** (simplest, reads tasks/activity)
5. **Iterate** — Agent Studio → My Space → Approvals → rest

---

## Appendix: SaarthiFlow Color Palette (for Tailwind v4)

```css
/* globals.css */
@theme {
  --font-sans: "Plus Jakarta Sans", system-ui, sans-serif;
  
  --color-brand-50:  #f5f0ff;
  --color-brand-100: #ece3ff;
  --color-brand-200: #d9c8ff;
  --color-brand-400: #a98bff;
  --color-brand-500: #8b5cf6;
  --color-brand-600: #7c3aed;
  --color-brand-700: #6d28d9;
  --color-ink:       #241a45;
  
  --color-rose-100:  #ffe4e6;  /* High priority */
  --color-rose-600:  #e11d48;
  --color-amber-100: #fef3c7;  /* Medium priority */
  --color-amber-700: #b45309;
  --color-emerald-100: #dcfce7; /* Low priority */
  --color-emerald-700: #047857;
}

/* Glassmorphism utilities */
.glass {
  @apply bg-white/50 backdrop-blur-xl border border-white/70;
}
.glass-rise {
  @apply glass transition-shadow hover:shadow-lg;
}
.btn {
  @apply inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold
         bg-gradient-to-r from-brand-600 to-brand-700 text-white shadow
         hover:from-brand-700 hover:to-brand-800 transition-colors;
}
.btn2 {
  @apply inline-flex items-center justify-center gap-2 rounded-xl px-3 py-1.5 text-sm font-medium
         bg-white/80 hover:bg-brand-50 text-ink/80 border border-brand-200 transition;
}
.inp {
  @apply rounded-xl border border-brand-200 bg-white/80 px-3 py-2 text-sm outline-none
         focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500;
}
.chip {
  @apply inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold;
}
```

---

*Plan created: 2026-11-14 | For: AI Work Assistant → SaarthiFlow integration*